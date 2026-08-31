"""GovernanceCenterService — policy management, decisions, exceptions, violations."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class GovernancePolicy(BaseModel):
    """A governance policy with versioning."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    name: str
    version: int = 1
    conditions: dict[str, Any] = Field(default_factory=dict)
    effect: str = "allow"
    priority: int = 0
    scope: str = ""
    status: str = "active"
    created_at: str = ""


class GovernanceDecision(BaseModel):
    """A record of a governance decision."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    who: str
    what: str
    why: str = ""
    decision: str
    reason: str = ""
    policy_ids: tuple[str, ...] = Field(default_factory=tuple)
    created_at: str = ""


class GovernanceException(BaseModel):
    """An exception to a governance policy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    policy_id: str
    reason: str
    approver: str
    created_at: str = ""
    expires_at: str | None = None


class GovernanceViolation(BaseModel):
    """A recorded policy violation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    policy_id: str
    description: str
    severity: str = "medium"
    created_at: str = ""


class GovernanceMetrics(BaseModel):
    """Aggregated governance metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    total_policies: int
    active_policies: int
    total_decisions: int
    total_exceptions: int
    total_violations: int


class GovernanceCenterService:
    """Central governance service for policy management, decisions, exceptions, and violations.

    All operations are tenant-scoped.
    """

    def __init__(self) -> None:
        self._policies: dict[str, GovernancePolicy] = {}
        self._decisions: dict[str, GovernanceDecision] = {}
        self._exceptions: dict[str, GovernanceException] = {}
        self._violations: dict[str, GovernanceViolation] = {}
        self._log = get_logger("eaip.governance_center.service")

    def _policy_key(self, tenant_id: str, policy_id: str) -> str:
        return f"{tenant_id}:{policy_id}"

    # ── Policies ────────────────────────────────────────────────

    def register_policy(
        self,
        tenant_id: str,
        name: str,
        conditions: dict[str, Any] | None = None,
        effect: str = "allow",
        priority: int = 0,
        scope: str = "",
    ) -> GovernancePolicy:
        """Register a new governance policy."""
        existing = [
            p for k, p in self._policies.items()
            if k.startswith(f"{tenant_id}:") and p.name == name
        ]
        version = max((p.version for p in existing), default=0) + 1
        policy_id = f"gp-{uuid.uuid4().hex[:10]}"
        policy = GovernancePolicy(
            id=policy_id,
            tenant_id=tenant_id,
            name=name,
            version=version,
            conditions=conditions or {},
            effect=effect,
            priority=priority,
            scope=scope,
            status="active",
            created_at=utc_now().isoformat(),
        )
        self._policies[self._policy_key(tenant_id, policy_id)] = policy
        self._log.info("governance.policy.registered", policy_id=policy_id, name=name, version=version)
        return policy

    def get_policy(self, tenant_id: str, policy_id: str) -> GovernancePolicy | None:
        return self._policies.get(self._policy_key(tenant_id, policy_id))

    def list_policies(self, tenant_id: str) -> list[GovernancePolicy]:
        return [p for k, p in self._policies.items() if k.startswith(f"{tenant_id}:")]

    def evaluate_policy(
        self,
        tenant_id: str,
        policy_id: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Deterministically evaluate a policy against a context."""
        policy = self.get_policy(tenant_id, policy_id)
        if policy is None:
            return {"policy_id": policy_id, "result": "not_found", "allowed": False}
        allowed = True
        for key, expected in policy.conditions.items():
            actual = context.get(key)
            if actual != expected:
                allowed = False
                break
        if policy.effect == "deny":
            allowed = not allowed
        return {
            "policy_id": policy_id,
            "name": policy.name,
            "version": policy.version,
            "effect": policy.effect,
            "allowed": allowed,
        }

    # ── Decisions ───────────────────────────────────────────────

    def record_decision(
        self,
        tenant_id: str,
        who: str,
        what: str,
        decision: str,
        reason: str = "",
        why: str = "",
        policy_ids: list[str] | None = None,
    ) -> GovernanceDecision:
        """Record a governance decision."""
        decision_id = f"gd-{uuid.uuid4().hex[:10]}"
        rec = GovernanceDecision(
            id=decision_id,
            tenant_id=tenant_id,
            who=who,
            what=what,
            why=why,
            decision=decision,
            reason=reason,
            policy_ids=tuple(policy_ids or []),
            created_at=utc_now().isoformat(),
        )
        self._decisions[self._policy_key(tenant_id, decision_id)] = rec
        self._log.info("governance.decision.recorded", decision_id=decision_id, who=who, decision=decision)
        return rec

    def get_decisions(self, tenant_id: str) -> list[GovernanceDecision]:
        return [d for k, d in self._decisions.items() if k.startswith(f"{tenant_id}:")]

    # ── Exceptions ──────────────────────────────────────────────

    def record_exception(
        self,
        tenant_id: str,
        policy_id: str,
        reason: str,
        approver: str,
        expires_at: str | None = None,
    ) -> GovernanceException:
        """Record an exception to a policy."""
        exception_id = f"ge-{uuid.uuid4().hex[:10]}"
        exc = GovernanceException(
            id=exception_id,
            tenant_id=tenant_id,
            policy_id=policy_id,
            reason=reason,
            approver=approver,
            created_at=utc_now().isoformat(),
            expires_at=expires_at,
        )
        self._exceptions[self._policy_key(tenant_id, exception_id)] = exc
        self._log.info("governance.exception.recorded", exception_id=exception_id, policy_id=policy_id)
        return exc

    def get_exceptions(self, tenant_id: str) -> list[GovernanceException]:
        return [e for k, e in self._exceptions.items() if k.startswith(f"{tenant_id}:")]

    # ── Violations ──────────────────────────────────────────────

    def record_violation(
        self,
        tenant_id: str,
        policy_id: str,
        description: str,
        severity: str = "medium",
    ) -> GovernanceViolation:
        """Record a policy violation."""
        violation_id = f"gv-{uuid.uuid4().hex[:10]}"
        violation = GovernanceViolation(
            id=violation_id,
            tenant_id=tenant_id,
            policy_id=policy_id,
            description=description,
            severity=severity,
            created_at=utc_now().isoformat(),
        )
        self._violations[self._policy_key(tenant_id, violation_id)] = violation
        self._log.info("governance.violation.recorded", violation_id=violation_id, policy_id=policy_id)
        return violation

    def get_violations(self, tenant_id: str) -> list[GovernanceViolation]:
        return [v for k, v in self._violations.items() if k.startswith(f"{tenant_id}:")]

    # ── Metrics ─────────────────────────────────────────────────

    def get_governance_metrics(self, tenant_id: str) -> GovernanceMetrics:
        """Get aggregated governance metrics for a tenant."""
        policies = self.list_policies(tenant_id)
        return GovernanceMetrics(
            tenant_id=tenant_id,
            total_policies=len(policies),
            active_policies=sum(1 for p in policies if p.status == "active"),
            total_decisions=len(self.get_decisions(tenant_id)),
            total_exceptions=len(self.get_exceptions(tenant_id)),
            total_violations=len(self.get_violations(tenant_id)),
        )


__all__ = [
    "GovernanceCenterService",
    "GovernanceDecision",
    "GovernanceException",
    "GovernanceMetrics",
    "GovernancePolicy",
    "GovernanceViolation",
]
