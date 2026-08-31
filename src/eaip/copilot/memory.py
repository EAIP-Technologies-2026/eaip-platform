"""Governed personal enterprise memory for EAIP Conductor Phase 7.

This module composes the existing MemoryEngine, GovernancePolicy, and
AuditLogger. Memory is data only: retrieval never grants a tool permission or
changes the Conductor execution policy.
"""

from __future__ import annotations

import re
from datetime import timedelta
from typing import Any, ClassVar

from eaip.admin.audit import AuditLogger
from eaip.admin.models import AuditEntry, AuditOutcome
from eaip.copilot.governance import GovernancePolicy
from eaip.memory.engine import MemoryEngine
from eaip.memory.models import (
    MemoryDomain,
    MemoryItem,
    MemoryQuery,
    MemoryScope,
    MemorySensitivity,
    MemoryStatus,
    MemoryType,
)
from eaip.shared.identifiers import CorrelationId
from eaip.shared.time import utc_now


class MemoryPolicyError(PermissionError):
    """Raised when a memory operation violates the server policy."""


class GovernedMemoryService:
    """Authorize and execute bounded memory operations for an actor."""

    READ_PERMISSION = "copilot:memory:read"
    WRITE_PERMISSION = "copilot:memory:write"
    DELETE_PERMISSION = "copilot:memory:delete"
    ORGANIZATION_WRITE_PERMISSION = "copilot:memory:organization:write"
    SENSITIVE_PERMISSION = "copilot:memory:sensitive"

    _RETENTION_SECONDS: ClassVar[dict[MemoryDomain, int]] = {
        MemoryDomain.PERSONAL: 30 * 24 * 60 * 60,
        MemoryDomain.ORGANIZATION: 90 * 24 * 60 * 60,
        MemoryDomain.OPERATIONAL: 7 * 24 * 60 * 60,
        MemoryDomain.CONVERSATION: 24 * 60 * 60,
        MemoryDomain.INVESTIGATION: 7 * 24 * 60 * 60,
    }
    _SECRET_PATTERNS = (
        re.compile(r"(?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token)\s*[:=]", re.I),
        re.compile(r"(?:password|passwd|secret)\s*[:=]", re.I),
        re.compile(r"bearer\s+[A-Za-z0-9._~-]{12,}", re.I),
        re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.", re.I),
    )
    _SENSITIVE_PATTERNS = (
        re.compile(r"\b(?:ssn|social security|credit card|bank account|medical)\b", re.I),
        re.compile(r"\b(?:pii|personal data|confidential)\b", re.I),
    )

    def __init__(
        self,
        engine: MemoryEngine,
        governance: GovernancePolicy,
        audit: AuditLogger,
    ) -> None:
        """Initialize the service with existing platform primitives."""
        self._engine = engine
        self._governance = governance
        self._audit = audit

    @property
    def engine(self) -> MemoryEngine:
        """Return the composed MemoryEngine."""
        return self._engine

    def actor_id(self, user: dict[str, Any]) -> str:
        """Derive the actor from authenticated claims, never request data."""
        return str(user.get("sub") or user.get("name") or "unknown")

    def tenant_id(self, user: dict[str, Any]) -> str:
        """Derive the tenant from authenticated claims, with a safe local default."""
        return str(
            user.get("organization_id")
            or user.get("org_id")
            or user.get("tenant_id")
            or "default"
        )

    def scope_for(self, user: dict[str, Any], domain: MemoryDomain) -> MemoryScope:
        """Build a server-authoritative scope for a memory domain."""
        tenant = self.tenant_id(user)
        actor = self.actor_id(user)
        if domain in (MemoryDomain.ORGANIZATION, MemoryDomain.OPERATIONAL):
            return MemoryScope(tenant_id=tenant, application_id=domain.value)
        return MemoryScope(tenant_id=tenant, user_id=actor, application_id=domain.value)

    def visible_scopes(self, user: dict[str, Any]) -> tuple[MemoryScope, ...]:
        """Return bounded scopes visible to the authenticated actor."""
        return tuple(self.scope_for(user, domain) for domain in MemoryDomain)

    async def create(
        self,
        user: dict[str, Any],
        *,
        content: str,
        domain: MemoryDomain = MemoryDomain.PERSONAL,
        importance: float = 0.6,
        tags: tuple[str, ...] = (),
    ) -> MemoryItem:
        """Create explicit, policy-classified memory in the actor's scope."""
        self._require(user, self.WRITE_PERMISSION, domain=domain)
        normalized = content.strip()
        if not normalized:
            raise MemoryPolicyError("Memory content is required")
        sensitivity = self._classify(normalized, domain)
        if sensitivity is MemorySensitivity.NEVER_STORE:
            self._audit_policy_denial(user, "memory.create", "secret content")
            raise MemoryPolicyError("Secrets and credentials must never be stored in memory")
        if sensitivity in (MemorySensitivity.SENSITIVE, MemorySensitivity.RESTRICTED):
            self._require(user, self.SENSITIVE_PERMISSION, domain=domain)

        now = utc_now()
        memory_type = self._memory_type(domain)
        item = await self._engine.create_memory(
            normalized,
            memory_type,
            self.scope_for(user, domain),
            importance=importance,
            tags=tuple(tags[:8]),
            expires_at=now + timedelta(seconds=self._RETENTION_SECONDS[domain]),
            domain=domain,
            confidence=1.0,
            sensitivity=sensitivity,
            source="conductor",
            provenance="user_explicit",
            retention_policy=f"{self._RETENTION_SECONDS[domain]}s",
        )
        self._audit_operation(user, "memory.created", item, AuditOutcome.SUCCESS)
        return item

    async def list_memories(self, user: dict[str, Any], query: str = "") -> list[MemoryItem]:
        """List bounded active memories visible to the actor."""
        self._require(user, self.READ_PERMISSION)
        visible: list[MemoryItem] = []
        for scope in self.visible_scopes(user):
            items = await self._engine.store.list_by_scope(scope, status="active", limit=100)
            visible.extend(item for item in items if self._is_visible(item, query))
        visible.sort(key=lambda item: (item.importance, item.updated_at), reverse=True)
        return visible[:100]

    async def retrieve(
        self,
        user: dict[str, Any],
        query: str = "",
        limit: int = 8,
    ) -> list[MemoryItem]:
        """Retrieve bounded, non-expired memory with explicit provenance."""
        self._require(user, self.READ_PERMISSION)
        results: list[MemoryItem] = []
        safe_limit = max(1, min(limit, 12))
        for scope in self.visible_scopes(user):
            result = await self._engine.search_memories(
                MemoryQuery(
                    query=query.strip(),
                    scopes=(scope,),
                    status=MemoryStatus.ACTIVE,
                    limit=safe_limit,
                )
            )
            results.extend(
                item.memory
                for item in result.results
                if self._is_visible(item.memory, query)
            )
        results.sort(key=lambda item: (item.importance, item.updated_at), reverse=True)
        return results[:safe_limit]

    async def get(self, user: dict[str, Any], memory_id: str) -> MemoryItem | None:
        """Read one memory only when its full server-derived scope is visible."""
        self._require(user, self.READ_PERMISSION)
        for scope in self.visible_scopes(user):
            item = await self._engine.get_memory(memory_id, scope)
            if item is not None and self._is_visible(item):
                return item
        return None

    async def forget(
        self,
        user: dict[str, Any],
        *,
        memory_id: str | None = None,
        query: str | None = None,
    ) -> int:
        """Delete visible memory explicitly requested by the actor."""
        self._require(user, self.DELETE_PERMISSION)
        targets: list[MemoryItem] = []
        if memory_id:
            item = await self.get(user, memory_id)
            if item is not None:
                targets = [item]
        elif query:
            targets = await self.retrieve(user, query, limit=12)
        deleted = 0
        for item in targets:
            if item.domain is MemoryDomain.ORGANIZATION:
                self._require(user, self.ORGANIZATION_WRITE_PERMISSION, domain=item.domain)
            if await self._engine.delete_memory(
                item.memory_id,
                item.scope,
                reason="explicit_forget",
            ):
                self._audit_operation(user, "memory.deleted", item, AuditOutcome.SUCCESS)
                deleted += 1
        return deleted

    def serialize(self, item: MemoryItem) -> dict[str, Any]:
        """Expose inspectable memory metadata without authorization-bearing claims."""
        return {
            "id": item.memory_id,
            "domain": item.domain.value,
            "content": item.content,
            "source": item.source,
            "provenance": "MEMORY",
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
            "accessed_at": item.accessed_at.isoformat() if item.accessed_at else None,
            "importance": item.importance,
            "confidence": item.confidence,
            "sensitivity": item.sensitivity.value,
            "retention_policy": item.retention_policy,
            "expires_at": item.expires_at.isoformat() if item.expires_at else None,
            "status": item.status.value,
        }

    def _require(
        self,
        user: dict[str, Any],
        permission: str,
        *,
        domain: MemoryDomain | None = None,
    ) -> None:
        """Enforce permissions from server-authenticated roles only."""
        roles = [str(role) for role in (user.get("roles") or [])]
        permissions = self._governance.role_permissions(roles)
        if permission not in permissions and "*" not in permissions:
            raise MemoryPolicyError("You do not have permission for this memory operation")
        if (
            domain is MemoryDomain.ORGANIZATION
            and permission != self.ORGANIZATION_WRITE_PERMISSION
        ):
            return

    def _classify(self, content: str, domain: MemoryDomain) -> MemorySensitivity:
        if any(pattern.search(content) for pattern in self._SECRET_PATTERNS):
            return MemorySensitivity.NEVER_STORE
        if domain is MemoryDomain.ORGANIZATION:
            return MemorySensitivity.RESTRICTED
        if any(pattern.search(content) for pattern in self._SENSITIVE_PATTERNS):
            return MemorySensitivity.SENSITIVE
        return MemorySensitivity.INFORMATIONAL

    @staticmethod
    def _memory_type(domain: MemoryDomain) -> MemoryType:
        if domain is MemoryDomain.CONVERSATION:
            return MemoryType.SESSION
        if domain in (MemoryDomain.OPERATIONAL, MemoryDomain.INVESTIGATION):
            return MemoryType.EPISODIC
        return MemoryType.LONG_TERM

    @staticmethod
    def _is_visible(item: MemoryItem, query: str = "") -> bool:
        now = utc_now()
        if item.status is not MemoryStatus.ACTIVE:
            return False
        if item.expires_at is not None and item.expires_at <= now:
            return False
        return not query or query.lower() in item.content.lower() or any(
            query.lower() in tag.lower() for tag in item.tags
        )

    def _audit_operation(
        self,
        user: dict[str, Any],
        action: str,
        item: MemoryItem,
        outcome: AuditOutcome,
    ) -> None:
        self._audit.log(
            AuditEntry(
                id=f"audit-memory-{CorrelationId.new()}",
                actor_id=self.actor_id(user),
                action=action,
                resource_type="memory",
                resource_id=item.memory_id,
                outcome=outcome,
                details={
                    "domain": item.domain.value,
                    "scope": item.scope.scope_key(),
                    "sensitivity": item.sensitivity.value,
                },
                correlation_id=str(CorrelationId.new()),
            )
        )

    def _audit_policy_denial(self, user: dict[str, Any], action: str, reason: str) -> None:
        self._audit.log(
            AuditEntry(
                id=f"audit-memory-denied-{CorrelationId.new()}",
                actor_id=self.actor_id(user),
                action=action,
                resource_type="memory",
                resource_id="policy",
                outcome=AuditOutcome.FAILURE,
                details={"error": reason},
                correlation_id=str(CorrelationId.new()),
            )
        )


__all__ = ["GovernedMemoryService", "MemoryPolicyError"]
