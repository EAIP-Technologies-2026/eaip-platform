"""InvestigationService — manages persistent enterprise investigation lifecycle.

An investigation is a bounded, governed analytical session.  It composes:
- Existing Conductor tools for evidence collection
- GovernedMemoryService for context retrieval
- AuditLogger for immutable audit trail
- EventBus for domain events

It does NOT create a parallel execution pathway.  All tool access goes
through the existing governance pipeline.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from eaip.admin.audit import AuditLogger
from eaip.admin.models import AuditEntry, AuditOutcome
from eaip.copilot.governance import GovernancePolicy
from eaip.copilot.investigation.models import (
    CreateInvestigationRequest,
    Evidence,
    EvidenceSource,
    EvidenceType,
    Hypothesis,
    Investigation,
    InvestigationStatus,
    TimelineEvent,
)
from eaip.copilot.memory import GovernedMemoryService
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.identifiers import CorrelationId
from eaip.shared.time import utc_now

# Valid state transitions.
_TRANSITIONS: dict[
    InvestigationStatus, frozenset[InvestigationStatus]
] = {
    InvestigationStatus.DRAFT: frozenset(
        {InvestigationStatus.ACTIVE, InvestigationStatus.CANCELLED}
    ),
    InvestigationStatus.ACTIVE: frozenset(
        {
            InvestigationStatus.PAUSED,
            InvestigationStatus.WAITING,
            InvestigationStatus.RESOLVED,
            InvestigationStatus.CANCELLED,
        }
    ),
    InvestigationStatus.PAUSED: frozenset(
        {
            InvestigationStatus.ACTIVE,
            InvestigationStatus.CANCELLED,
        }
    ),
    InvestigationStatus.WAITING: frozenset(
        {
            InvestigationStatus.ACTIVE,
            InvestigationStatus.RESOLVED,
            InvestigationStatus.CANCELLED,
        }
    ),
    InvestigationStatus.RESOLVED: frozenset(
        {
            InvestigationStatus.ARCHIVED,
            InvestigationStatus.ACTIVE,
        }
    ),
    InvestigationStatus.ARCHIVED: frozenset(set()),
    InvestigationStatus.CANCELLED: frozenset(set()),
}

_RETENTION_SECONDS: dict[str, int] = {
    "low": 7 * 24 * 60 * 60,
    "medium": 30 * 24 * 60 * 60,
    "high": 90 * 24 * 60 * 60,
    "critical": 180 * 24 * 60 * 60,
}


_STALE_THRESHOLD_SECONDS = 3600


class InvestigationService:
    """Manage persistent enterprise investigations with full governance.

    Investigations are owned by a user within a tenant.  Evidence is
    classified as OBSERVED/INFERRED/RECOMMENDED with provenance.  All
    operations are audited.  Memory integration provides historical context
    but never grants authorization.
    """

    READ_PERMISSION = "copilot:investigations:read"
    WRITE_PERMISSION = "copilot:investigations:write"
    DELETE_PERMISSION = "copilot:investigations:delete"

    def __init__(
        self,
        *,
        governance: GovernancePolicy,
        audit: AuditLogger,
        memory_service: GovernedMemoryService | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize with existing platform primitives."""
        self._governance = governance
        self._audit = audit
        self._memory = memory_service
        self._event_bus = event_bus
        self._log = get_logger("eaip.copilot.investigation")
        self._investigations: dict[str, Investigation] = {}
        self._evidence: dict[str, list[Evidence]] = {}
        self._timelines: dict[str, list[TimelineEvent]] = {}
        self._hypotheses: dict[str, list[Hypothesis]] = {}

    async def create(
        self,
        user: dict[str, Any],
        request: CreateInvestigationRequest,
    ) -> Investigation:
        """Create a new investigation in DRAFT status."""
        actor = self._actor(user)
        tenant = self._tenant(user)
        self._require_permission(user, self.WRITE_PERMISSION)

        inv_id = f"inv-{uuid.uuid4().hex[:12]}"
        now = utc_now()
        retention = _RETENTION_SECONDS.get(
            request.priority.value, 30 * 24 * 60 * 60
        )

        investigation = Investigation(
            id=inv_id,
            tenant_id=tenant,
            owner_id=actor,
            title=request.title,
            objective=request.objective,
            status=InvestigationStatus.DRAFT,
            priority=request.priority,
            related_entities=request.related_entities,
            related_routes=request.related_routes,
            created_at=now,
            updated_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(seconds=retention),
            retention_policy=f"{retention}s",
        )
        self._investigations[inv_id] = investigation
        self._evidence[inv_id] = []
        self._timelines[inv_id] = []
        self._hypotheses[inv_id] = []

        self._add_timeline(
            inv_id, actor, "created", f"Investigation created: {request.title}"
        )
        self._audit_log(
            actor, "investigation.created", inv_id, tenant
        )
        self._log.info(
            "investigation.created",
            investigation_id=inv_id,
            actor=actor,
            tenant=tenant,
        )
        return investigation

    async def get(
        self, user: dict[str, Any], investigation_id: str
    ) -> Investigation | None:
        """Retrieve an investigation visible to the user."""
        self._require_permission(user, self.READ_PERMISSION)
        inv = self._investigations.get(investigation_id)
        if inv is None:
            return None
        if not self._is_visible(user, inv):
            return None
        return inv

    async def list_investigations(
        self,
        user: dict[str, Any],
        *,
        status: InvestigationStatus | None = None,
        limit: int = 20,
    ) -> list[Investigation]:
        """List investigations visible to the user."""
        self._require_permission(user, self.READ_PERMISSION)
        results: list[Investigation] = []
        for inv in self._investigations.values():
            if not self._is_visible(user, inv):
                continue
            if status and inv.status is not status:
                continue
            results.append(inv)
        results.sort(key=lambda i: i.last_activity_at, reverse=True)
        return results[:limit]

    async def start(
        self, user: dict[str, Any], investigation_id: str
    ) -> Investigation:
        """Transition an investigation from DRAFT to ACTIVE."""
        return await self._transition(
            user, investigation_id, InvestigationStatus.ACTIVE, "started"
        )

    async def pause(
        self, user: dict[str, Any], investigation_id: str
    ) -> Investigation:
        """Pause an active investigation."""
        return await self._transition(
            user, investigation_id, InvestigationStatus.PAUSED, "paused"
        )

    async def resume(
        self, user: dict[str, Any], investigation_id: str
    ) -> Investigation:
        """Resume a paused investigation."""
        return await self._transition(
            user, investigation_id, InvestigationStatus.ACTIVE, "resumed"
        )

    async def resolve(
        self,
        user: dict[str, Any],
        investigation_id: str,
        summary: str = "",
        findings: tuple[str, ...] = (),
        recommendations: tuple[str, ...] = (),
    ) -> Investigation:
        """Resolve an investigation with findings and recommendations."""
        actor = self._actor(user)
        inv = await self._transition(
            user, investigation_id, InvestigationStatus.RESOLVED, "resolved"
        )
        update: dict[str, Any] = {
            "updated_at": utc_now(),
            "last_activity_at": utc_now(),
            "completed_at": utc_now(),
        }
        if summary:
            update["summary"] = summary
        if findings:
            update["findings"] = findings
        if recommendations:
            update["recommendations"] = recommendations
        inv = inv.model_copy(update=update)
        self._investigations[investigation_id] = inv

        self._add_timeline(
            investigation_id, actor, "resolved",
            summary or "Investigation resolved.",
        )
        self._audit_log(
            actor, "investigation.resolved", investigation_id,
            inv.tenant_id,
        )
        return inv

    async def archive(
        self, user: dict[str, Any], investigation_id: str
    ) -> Investigation:
        """Archive a resolved investigation."""
        return await self._transition(
            user, investigation_id, InvestigationStatus.ARCHIVED, "archived"
        )

    async def cancel(
        self, user: dict[str, Any], investigation_id: str
    ) -> Investigation:
        """Cancel an investigation."""
        return await self._transition(
            user, investigation_id, InvestigationStatus.CANCELLED, "cancelled"
        )

    async def add_evidence(
        self,
        user: dict[str, Any],
        investigation_id: str,
        *,
        evidence_type: EvidenceType,
        source: EvidenceSource,
        content: str,
        source_tool: str = "",
        source_route: str = "",
        confidence: float = 1.0,
        correlation_id: str = "",
    ) -> Evidence:
        """Add classified evidence to an investigation."""
        actor = self._actor(user)
        inv = await self._get_owned(user, investigation_id)

        if inv.status not in (
            InvestigationStatus.ACTIVE,
            InvestigationStatus.WAITING,
        ):
            raise ValueError(
                "Evidence can only be added to active investigations"
            )

        evidence_id = f"ev-{uuid.uuid4().hex[:12]}"
        now = utc_now()

        # Detect stale evidence: if source is a tool, mark as stale
        # if the investigation has been paused for more than 1 hour.
        stale = False
        stale_reason = ""
        gap = (now - inv.last_activity_at).total_seconds()
        if gap > _STALE_THRESHOLD_SECONDS:
            stale = True
            stale_reason = (
                f"Evidence collected after {int(gap)}s inactivity"
            )

        evidence = Evidence(
            id=evidence_id,
            investigation_id=investigation_id,
            evidence_type=evidence_type,
            source=source,
            content=content,
            source_tool=source_tool,
            source_route=source_route,
            confidence=confidence,
            timestamp=now,
            stale=stale,
            stale_reason=stale_reason,
            correlation_id=correlation_id or str(CorrelationId.new()),
        )
        self._evidence[investigation_id].append(evidence)

        inv = inv.model_copy(
            update={
                "updated_at": now,
                "last_activity_at": now,
                "reasoning_steps_used": inv.reasoning_steps_used + 1,
            }
        )
        self._investigations[investigation_id] = inv

        desc = f"{evidence_type.value.upper()}: {content[:100]}"
        self._add_timeline(
            investigation_id, actor, "evidence_added", desc,
            evidence_id=evidence_id,
        )
        self._audit_log(
            actor, "investigation.evidence_added", investigation_id,
            inv.tenant_id,
        )
        return evidence

    async def get_evidence(
        self, user: dict[str, Any], investigation_id: str
    ) -> list[Evidence]:
        """Get all evidence for an investigation."""
        self._require_permission(user, self.READ_PERMISSION)
        inv = self._investigations.get(investigation_id)
        if inv is None or not self._is_visible(user, inv):
            return []
        return list(self._evidence.get(investigation_id, []))

    async def add_hypothesis(
        self,
        user: dict[str, Any],
        investigation_id: str,
        *,
        statement: str,
        confidence: float = 0.5,
        supporting_ids: tuple[str, ...] = (),
        contradicting_ids: tuple[str, ...] = (),
    ) -> Hypothesis:
        """Add a hypothesis to an investigation."""
        actor = self._actor(user)
        inv = await self._get_owned(user, investigation_id)

        hyp_id = f"hyp-{uuid.uuid4().hex[:12]}"
        now = utc_now()
        hypothesis = Hypothesis(
            id=hyp_id,
            investigation_id=investigation_id,
            statement=statement,
            confidence=confidence,
            supporting_evidence_ids=supporting_ids,
            contradicting_evidence_ids=contradicting_ids,
            status="active",
            created_at=now,
            updated_at=now,
        )
        self._hypotheses[investigation_id].append(hypothesis)

        inv = inv.model_copy(
            update={"updated_at": now, "last_activity_at": now}
        )
        self._investigations[investigation_id] = inv

        self._add_timeline(
            investigation_id, actor, "hypothesis_added",
            f"Hypothesis: {statement[:100]}",
        )
        return hypothesis

    async def get_hypotheses(
        self, user: dict[str, Any], investigation_id: str
    ) -> list[Hypothesis]:
        """Get all hypotheses for an investigation."""
        self._require_permission(user, self.READ_PERMISSION)
        inv = self._investigations.get(investigation_id)
        if inv is None or not self._is_visible(user, inv):
            return []
        return list(self._hypotheses.get(investigation_id, []))

    async def get_timeline(
        self, user: dict[str, Any], investigation_id: str
    ) -> list[TimelineEvent]:
        """Get the timeline for an investigation."""
        self._require_permission(user, self.READ_PERMISSION)
        inv = self._investigations.get(investigation_id)
        if inv is None or not self._is_visible(user, inv):
            return []
        return list(self._timelines.get(investigation_id, []))

    async def update_findings(
        self,
        user: dict[str, Any],
        investigation_id: str,
        *,
        findings: tuple[str, ...] = (),
        recommendations: tuple[str, ...] = (),
        unresolved_questions: tuple[str, ...] = (),
        summary: str = "",
    ) -> Investigation:
        """Update investigation findings and recommendations."""
        actor = self._actor(user)
        inv = await self._get_owned(user, investigation_id)
        now = utc_now()
        update: dict[str, Any] = {
            "updated_at": now,
            "last_activity_at": now,
        }
        if findings:
            update["findings"] = findings
        if recommendations:
            update["recommendations"] = recommendations
        if unresolved_questions:
            update["unresolved_questions"] = unresolved_questions
        if summary:
            update["summary"] = summary
        inv = inv.model_copy(update=update)
        self._investigations[investigation_id] = inv

        self._add_timeline(
            investigation_id, actor, "findings_updated",
            "Investigation findings updated.",
        )
        return inv

    async def delete(
        self, user: dict[str, Any], investigation_id: str
    ) -> bool:
        """Delete an investigation (requires DELETE permission)."""
        actor = self._actor(user)
        self._require_permission(user, self.DELETE_PERMISSION)
        inv = self._investigations.get(investigation_id)
        if inv is None:
            return False
        if not self._is_owner(user, inv):
            raise PermissionError("Only the owner can delete an investigation")
        if inv.status in (
            InvestigationStatus.ARCHIVED,
            InvestigationStatus.CANCELLED,
        ):
            raise PermissionError(
                "Cannot delete archived or cancelled investigations"
            )

        tenant = self._tenant(user)
        del self._investigations[investigation_id]
        self._evidence.pop(investigation_id, None)
        self._timelines.pop(investigation_id, None)
        self._hypotheses.pop(investigation_id, None)

        self._audit_log(
            actor, "investigation.deleted", investigation_id, tenant
        )
        return True

    async def find_resumable(
        self, user: dict[str, Any], query: str = ""
    ) -> Investigation | None:
        """Find the most recent resumable investigation matching a query."""
        self._require_permission(user, self.READ_PERMISSION)
        resumable_statuses = {
            InvestigationStatus.ACTIVE,
            InvestigationStatus.PAUSED,
            InvestigationStatus.WAITING,
        }
        candidates: list[Investigation] = []
        for inv in self._investigations.values():
            if not self._is_visible(user, inv):
                continue
            if inv.status not in resumable_statuses:
                continue
            if (
                query
                and query.lower() not in inv.title.lower()
                and query.lower() not in inv.objective.lower()
            ):
                continue
            candidates.append(inv)
        if not candidates:
            return None
        candidates.sort(key=lambda i: i.last_activity_at, reverse=True)
        return candidates[0]

    def serialize(
        self, investigation: Investigation
    ) -> dict[str, Any]:
        """Serialize an investigation for API response."""
        return {
            "id": investigation.id,
            "tenant_id": investigation.tenant_id,
            "owner_id": investigation.owner_id,
            "title": investigation.title,
            "objective": investigation.objective,
            "status": investigation.status.value,
            "priority": investigation.priority.value,
            "current_stage": investigation.current_stage,
            "summary": investigation.summary,
            "findings": list(investigation.findings),
            "recommendations": list(investigation.recommendations),
            "unresolved_questions": list(
                investigation.unresolved_questions
            ),
            "evidence_count": len(
                self._evidence.get(investigation.id, [])
            ),
            "hypothesis_count": len(
                self._hypotheses.get(investigation.id, [])
            ),
            "reasoning_steps_used": investigation.reasoning_steps_used,
            "max_reasoning_steps": investigation.max_reasoning_steps,
            "created_at": investigation.created_at.isoformat(),
            "updated_at": investigation.updated_at.isoformat(),
            "last_activity_at": investigation.last_activity_at.isoformat(),
            "completed_at": (
                investigation.completed_at.isoformat()
                if investigation.completed_at
                else None
            ),
            "expires_at": (
                investigation.expires_at.isoformat()
                if investigation.expires_at
                else None
            ),
            "retention_policy": investigation.retention_policy,
            "provenance": investigation.provenance,
        }

    def serialize_evidence(self, evidence: Evidence) -> dict[str, Any]:
        """Serialize evidence for API response."""
        return {
            "id": evidence.id,
            "investigation_id": evidence.investigation_id,
            "evidence_type": evidence.evidence_type.value,
            "source": evidence.source.value,
            "content": evidence.content,
            "source_tool": evidence.source_tool,
            "source_route": evidence.source_route,
            "confidence": evidence.confidence,
            "timestamp": evidence.timestamp.isoformat(),
            "stale": evidence.stale,
            "stale_reason": evidence.stale_reason,
            "correlation_id": evidence.correlation_id,
        }

    def serialize_timeline(
        self, event: TimelineEvent
    ) -> dict[str, Any]:
        """Serialize a timeline event for API response."""
        return {
            "id": event.id,
            "investigation_id": event.investigation_id,
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "description": event.description,
            "actor_id": event.actor_id,
            "evidence_id": event.evidence_id,
        }

    # --- Private helpers ---

    def _add_timeline(
        self,
        investigation_id: str,
        actor: str,
        event_type: str,
        description: str,
        evidence_id: str = "",
    ) -> TimelineEvent:
        """Add an event to the investigation timeline."""
        event = TimelineEvent(
            id=f"tl-{uuid.uuid4().hex[:12]}",
            investigation_id=investigation_id,
            event_type=event_type,
            description=description,
            actor_id=actor,
            evidence_id=evidence_id,
        )
        self._timelines[investigation_id].append(event)
        return event

    async def _transition(
        self,
        user: dict[str, Any],
        investigation_id: str,
        target: InvestigationStatus,
        action: str,
    ) -> Investigation:
        """Transition an investigation to a new status."""
        actor = self._actor(user)
        inv = await self._get_owned(user, investigation_id)

        allowed = _TRANSITIONS.get(inv.status, frozenset())
        if target not in allowed:
            raise ValueError(
                f"Cannot transition from {inv.status.value} "
                f"to {target.value}"
            )

        inv = inv.model_copy(
            update={
                "status": target,
                "updated_at": utc_now(),
                "last_activity_at": utc_now(),
            }
        )
        self._investigations[investigation_id] = inv

        self._add_timeline(
            investigation_id, actor, action,
            f"Investigation {action}.",
        )
        self._audit_log(
            actor, f"investigation.{action}", investigation_id,
            inv.tenant_id,
        )
        return inv

    async def _get_owned(
        self, user: dict[str, Any], investigation_id: str
    ) -> Investigation:
        """Get an investigation and verify ownership."""
        inv = self._investigations.get(investigation_id)
        if inv is None:
            raise ValueError(
                f"Investigation not found: {investigation_id}"
            )
        if not self._is_owner(user, inv):
            raise PermissionError(
                "You do not own this investigation"
            )
        return inv

    def _is_owner(
        self, user: dict[str, Any], inv: Investigation
    ) -> bool:
        """Check if the user is the investigation owner."""
        return self._actor(user) == inv.owner_id

    def _is_visible(
        self, user: dict[str, Any], inv: Investigation
    ) -> bool:
        """Check if the user can see this investigation."""
        # Tenant must always match.
        if self._tenant(user) != inv.tenant_id:
            return False
        if self._is_owner(user, inv):
            return True
        # Admins can see all tenant investigations.
        roles = list(user.get("roles") or [])
        return "admin" in roles

    def _require_permission(
        self, user: dict[str, Any], permission: str
    ) -> None:
        """Enforce permissions from server-authenticated roles."""
        roles = list(user.get("roles") or [])
        permissions = self._governance.role_permissions(roles)
        if permission not in permissions and "*" not in permissions:
            raise PermissionError(
                "You do not have permission for this operation"
            )

    def _audit_log(
        self,
        actor: str,
        action: str,
        resource_id: str,
        tenant: str,
    ) -> None:
        """Write an audit entry."""
        self._audit.log(
            AuditEntry(
                id=f"audit-inv-{uuid.uuid4().hex[:12]}",
                actor_id=actor,
                action=action,
                resource_type="investigation",
                resource_id=resource_id,
                outcome=AuditOutcome.SUCCESS,
                details={"tenant_id": tenant},
                correlation_id=str(CorrelationId.new()),
            )
        )

    @staticmethod
    def _actor(user: dict[str, Any]) -> str:
        """Extract actor from authenticated claims."""
        return str(user.get("sub") or user.get("name") or "unknown")

    @staticmethod
    def _tenant(user: dict[str, Any]) -> str:
        """Extract tenant from authenticated claims."""
        return str(
            user.get("organization_id")
            or user.get("org_id")
            or user.get("tenant_id")
            or "default"
        )


__all__ = ["InvestigationService"]
