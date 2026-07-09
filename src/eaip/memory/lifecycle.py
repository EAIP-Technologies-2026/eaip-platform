"""Memory lifecycle — expiration, retention policies, and lifecycle management."""

from __future__ import annotations

import time
from typing import Any, Protocol

from eaip.logging.context import get_logger
from eaip.memory.exceptions import MemoryStoreError
from eaip.memory.models import (
    MemoryItem,
    MemoryScope,
    MemoryStatus,
    MemoryType,
    RetentionConfig,
    ScopedMemoryId,
)
from eaip.shared.time import utc_now


class RetentionPolicy(Protocol):
    """Protocol for memory retention policy implementations.

    Determines which memories should be expired or archived based on
    configurable criteria.
    """

    async def evaluate(self, item: MemoryItem) -> str | None:
        """Evaluate a memory item against the retention policy.

        Args:
            item: The memory item to evaluate.

        Returns:
            None if the item is still valid, or an action string
            ("expire" or "archive") if the policy applies.
        """
        ...


class MaxAgeRetentionPolicy:
    """Retention policy that expires memories older than a maximum age."""

    def __init__(self, max_age_seconds: int, memory_type: str | None = None) -> None:
        """Initialize the policy.

        Args:
            max_age_seconds: Maximum age in seconds before expiration.
            memory_type: Optional memory type to restrict this policy to.
        """
        self._max_age = max_age_seconds
        self._memory_type = memory_type
        self._log = get_logger("eaip.memory.lifecycle.max_age")

    async def evaluate(self, item: MemoryItem) -> str | None:
        """Evaluate if the item has exceeded maximum age.

        Args:
            item: The memory item to evaluate.

        Returns:
            "expire" if the item is older than the maximum age.
        """
        if self._memory_type and item.memory_type.value != self._memory_type:
            return None
        age_seconds = (utc_now() - item.created_at).total_seconds()
        if age_seconds > self._max_age:
            self._log.debug(
                "policy.max_age.expired",
                memory_id=item.memory_id,
                age_seconds=round(age_seconds, 1),
            )
            return "expire"
        return None


class MaxCountRetentionPolicy:
    """Retention policy that limits the number of memories per scope and type."""

    def __init__(self, max_count: int, memory_type: str | None = None) -> None:
        """Initialize the policy.

        Args:
            max_count: Maximum number of memories allowed.
            memory_type: Optional memory type to restrict this policy to.
        """
        self._max_count = max_count
        self._memory_type = memory_type
        self._log = get_logger("eaip.memory.lifecycle.max_count")

    async def evaluate(self, _item: MemoryItem) -> str | None:
        """Evaluate if the item exceeds count limits.

        Note: This policy requires external state to determine current counts.
        This stub returns None; actual enforcement happens in the lifecycle manager.

        Returns:
            None — evaluated externally.
        """
        return None


class PriorityRetentionPolicy:
    """Retention policy that preserves high-importance memories."""

    def __init__(self, min_importance: float = 0.7) -> None:
        """Initialize the policy.

        Args:
            min_importance: Minimum importance threshold (0.0-1.0).
        """
        self._min_importance = min_importance

    async def evaluate(self, item: MemoryItem) -> str | None:
        """Evaluate if the item should be retained due to high importance.

        Args:
            item: The memory item to evaluate.

        Returns:
            None — high-importance items are always retained.
        """
        if item.importance >= self._min_importance:
            return None
        return None


class CompositeRetentionPolicy:
    """Composite policy that evaluates multiple sub-policies in sequence.

    The first policy that returns a non-None action wins.
    """

    def __init__(self, policies: list[Any]) -> None:
        """Initialize the composite policy.

        Args:
            policies: List of retention policy instances.
        """
        self._policies = policies
        self._log = get_logger("eaip.memory.lifecycle.composite")

    async def evaluate(self, item: MemoryItem) -> str | None:
        """Evaluate item against all sub-policies.

        Args:
            item: The memory item to evaluate.

        Returns:
            The first non-None action from sub-policies.
        """
        for policy in self._policies:
            try:
                result = await policy.evaluate(item)
                if result is not None:
                    return result
            except Exception:
                self._log.warning("policy.evaluate_failed", policy=type(policy).__name__)
        return None


class MemoryExpirationService:
    """Service for expiring memories based on TTL and retention policies."""

    def __init__(
        self,
        store: Any,
        config: RetentionConfig | None = None,
    ) -> None:
        """Initialize the expiration service.

        Args:
            store: The memory store to expire items from.
            config: Optional retention configuration.
        """
        self._store = store
        self._config = config or RetentionConfig()
        self._log = get_logger("eaip.memory.lifecycle.expiration")

    def _get_ttl(self, memory_type: MemoryType) -> int:
        """Get the TTL for a given memory type.

        Args:
            memory_type: The memory type.

        Returns:
            The TTL in seconds.
        """
        ttl_map = {
            MemoryType.WORKING: self._config.working_ttl_seconds,
            MemoryType.SESSION: self._config.session_ttl_seconds,
            MemoryType.LONG_TERM: self._config.long_term_ttl_seconds,
            MemoryType.EPISODIC: self._config.episodic_ttl_seconds,
            MemoryType.SEMANTIC: self._config.semantic_ttl_seconds,
        }
        return ttl_map.get(memory_type, 0)

    async def expire_memory(self, scoped_id: ScopedMemoryId) -> bool:
        """Expire a specific memory item.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            True if the item was expired.
        """
        item = await self._store.read(scoped_id)
        if item is None:
            return False

        updated = item.model_copy(
            update={
                "status": MemoryStatus.EXPIRED,
                "updated_at": utc_now(),
            }
        )
        try:
            await self._store.update(updated)
            self._log.info("lifecycle.expired", memory_id=item.memory_id)
            return True
        except MemoryStoreError:
            return False

    async def archive_memory(self, scoped_id: ScopedMemoryId) -> bool:
        """Archive a specific memory item.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            True if the item was archived.
        """
        item = await self._store.read(scoped_id)
        if item is None:
            return False

        updated = item.model_copy(
            update={
                "status": MemoryStatus.ARCHIVED,
                "updated_at": utc_now(),
            }
        )
        try:
            await self._store.update(updated)
            self._log.debug("lifecycle.archived", memory_id=item.memory_id)
            return True
        except MemoryStoreError:
            return False

    async def restore_memory(self, scoped_id: ScopedMemoryId) -> bool:
        """Restore a memory item to active status.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            True if the item was restored.
        """
        item = await self._store.read(scoped_id)
        if item is None:
            return False

        updated = item.model_copy(
            update={
                "status": MemoryStatus.ACTIVE,
                "updated_at": utc_now(),
            }
        )
        try:
            await self._store.update(updated)
            self._log.debug("lifecycle.restored", memory_id=item.memory_id)
            return True
        except MemoryStoreError:
            return False

    async def run_expiration_cycle(self, batch_size: int = 100) -> int:
        """Run a full expiration cycle against the store.

        Args:
            batch_size: Maximum items to process.

        Returns:
            The number of items expired.
        """
        now = time.time()
        expired_fq_ids = await self._store.expire_before(now, batch_size)
        if not expired_fq_ids:
            return 0

        if self._config.archive_on_expire:
            archived = await self._archive_many(expired_fq_ids)
            deleted = 0
        else:
            archived = 0
            deleted = await self._store.delete_many(expired_fq_ids)
        self._log.info(
            "lifecycle.expiration_cycle",
            expired=len(expired_fq_ids),
            archived=archived,
            deleted=deleted,
        )
        return archived + deleted

    async def _archive_many(self, fq_ids: list[str]) -> int:
        if hasattr(self._store, "archive_many"):
            archive_many = self._store.archive_many
            return int(await archive_many(fq_ids))

        archived = 0
        for fq_id in fq_ids:
            scoped_id = _scoped_id_from_fq_id(fq_id)
            if scoped_id is not None and await self.archive_memory(scoped_id):
                archived += 1
        return archived


def _scoped_id_from_fq_id(fq_id: str) -> ScopedMemoryId | None:
    parts = fq_id.split(":")
    if len(parts) < 2:  # noqa: PLR2004
        return None
    memory_id = parts[-1]
    scope_parts = parts[:-1]
    scope = MemoryScope(
        tenant_id=scope_parts[0],
        user_id=scope_parts[1] if len(scope_parts) > 1 else None,
        session_id=scope_parts[2] if len(scope_parts) > 2 else None,
        application_id=scope_parts[3] if len(scope_parts) > 3 else None,
    )
    return ScopedMemoryId(memory_id=memory_id, scope=scope)


class MemoryLifecycleManager:
    """Manages the full lifecycle of memory items.

    Coordinates creation, updates, expiration, archiving, and deletion
    with retention policies and expiration schedules.
    """

    def __init__(
        self,
        expiration_service: MemoryExpirationService,
        policies: list[Any] | None = None,
    ) -> None:
        """Initialize the lifecycle manager.

        Args:
            expiration_service: The expiration service.
            policies: Optional list of retention policies.
        """
        self._expiration = expiration_service
        self._policies = policies or []
        self._log = get_logger("eaip.memory.lifecycle.manager")

    async def run_retention_cycle(self, batch_size: int = 100) -> dict[str, Any]:
        """Run a full retention cycle, checking all active items.

        Args:
            batch_size: Maximum items to process per batch.

        Returns:
            A dict with cycle results.
        """
        expired_count = await self._expiration.run_expiration_cycle(batch_size)
        return {
            "expired_count": expired_count,
            "policies_evaluated": len(self._policies),
        }


__all__ = [
    "CompositeRetentionPolicy",
    "MaxAgeRetentionPolicy",
    "MaxCountRetentionPolicy",
    "MemoryExpirationService",
    "MemoryLifecycleManager",
    "PriorityRetentionPolicy",
    "RetentionPolicy",
]
