"""MemoryEngine — high-level API for the enterprise memory system."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from eaip.logging.context import get_logger
from eaip.memory.base import MemoryHook, MemoryStore, MemorySummarizer
from eaip.memory.consolidation import (
    ConsolidationReport,
    MemoryConsolidationService,
)
from eaip.memory.events import (
    MemoryArchived,
    MemoryConsolidated,
    MemoryCreated,
    MemoryDeleted,
    MemoryEngineEvent,
    MemoryExpired,
    MemoryRetrieved,
    MemorySearchExecuted,
    MemorySummarized,
    MemoryUpdated,
)
from eaip.memory.exceptions import (
    MemoryEngineError,
    MemoryError,
    MemoryNotFoundError,
)
from eaip.memory.lifecycle import MemoryExpirationService, MemoryLifecycleManager
from eaip.memory.models import (
    ConsolidationConfig,
    MemoryConfig,
    MemoryDomain,
    MemoryItem,
    MemoryQuery,
    MemoryResult,
    MemoryScope,
    MemorySensitivity,
    MemoryStatus,
    MemoryType,
    RetentionConfig,
    ScopedMemoryId,
)
from eaip.memory.registry import MemoryRegistry
from eaip.memory.retrieval import MemoryRetrievalService
from eaip.shared.time import utc_now


class MemoryEngine:
    """High-level API for enterprise memory management.

    Orchestrates memory creation, retrieval, search, update, deletion,
    lifecycle management, consolidation, and summarization across all
    memory types (working, session, long-term, episodic, semantic).

    Integrates with the Knowledge Engine for vector-backed storage,
    the Policy Engine for authorization, and the Event Bus for
    domain event publishing.
    """

    def __init__(
        self,
        store: MemoryStore,
        *,
        config: MemoryConfig | None = None,
        retention: RetentionConfig | None = None,
        consolidation: ConsolidationConfig | None = None,
        registry: MemoryRegistry | None = None,
        summarizer: MemorySummarizer | None = None,
        retrieval_service: MemoryRetrievalService | None = None,
        consolidation_service: MemoryConsolidationService | None = None,
        authorize_fn: Callable[[str, MemoryScope], None] | None = None,
        event_publisher: Callable[[object], None] | None = None,
        hooks: dict[str, list[MemoryHook]] | None = None,
        **_kwargs: object,
    ) -> None:
        """Initialize the MemoryEngine.

        Args:
            store: The memory store backend.
            config: Optional memory engine configuration.
            retention: Optional retention configuration.
            consolidation: Optional consolidation configuration.
            registry: Optional memory registry instance.
            summarizer: Optional memory summarizer.
            retrieval_service: Optional retrieval service.
            consolidation_service: Optional consolidation service.
            authorize_fn: Optional authorization callback.
            event_publisher: Optional event publisher for domain events.
            hooks: Optional dict of lifecycle hooks.
        """
        self._config = config or MemoryConfig()
        self._store = store
        self._registry = registry or MemoryRegistry()
        self._summarizer = summarizer

        self._retrieval = retrieval_service or MemoryRetrievalService(store)

        consol_config = consolidation or ConsolidationConfig()
        self._consolidation = consolidation_service or MemoryConsolidationService(
            config=consol_config,
        )

        ret_config = retention or RetentionConfig()
        self._expiration = MemoryExpirationService(store, ret_config)
        self._lifecycle = MemoryLifecycleManager(self._expiration)

        self._authorize_fn = authorize_fn
        self._event_publisher = event_publisher
        self._hooks = hooks or {}
        self._log = get_logger("eaip.memory.engine")

    @property
    def store(self) -> MemoryStore:
        """Return the underlying memory store."""
        return self._store

    @property
    def registry(self) -> MemoryRegistry:
        """Return the memory registry."""
        return self._registry

    @property
    def retrieval(self) -> MemoryRetrievalService:
        """Return the retrieval service."""
        return self._retrieval

    @property
    def lifecycle(self) -> MemoryLifecycleManager:
        """Return the lifecycle manager."""
        return self._lifecycle

    async def create_memory(
        self,
        content: str,
        memory_type: MemoryType,
        scope: MemoryScope,
        *,
        importance: float | None = None,
        tags: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
        parent_id: str | None = None,
        expires_at: datetime | None = None,
        embedding: tuple[float, ...] = (),
        domain: MemoryDomain = MemoryDomain.PERSONAL,
        confidence: float = 1.0,
        sensitivity: MemorySensitivity = MemorySensitivity.INFORMATIONAL,
        source: str = "memory_engine",
        provenance: str = "system",
        retention_policy: str = "standard",
    ) -> MemoryItem:
        """Create a new memory item.

        Args:
            content: The memory content.
            memory_type: The type of memory.
            scope: The memory scope (tenant, user, session).
            importance: Optional importance (0.0-1.0).
            tags: Optional tags for categorization.
            metadata: Optional metadata dict.
            parent_id: Optional parent memory ID.
            expires_at: Optional expiration time.
            embedding: Optional embedding vector.
            domain: Governed ownership domain.
            confidence: Confidence score for the stored context.
            sensitivity: Server-derived sensitivity classification.
            source: Source system for the memory.
            provenance: Provenance label for the memory.
            retention_policy: Retention policy identifier.

        Returns:
            The created MemoryItem.

        Raises:
            MemoryValidationError: If validation fails.
            MemoryEngineError: If the engine encounters an error.
        """
        if self._authorize_fn:
            self._authorize_fn("create_memory", scope)

        self._run_hooks("before_store", scope)

        imp = importance if importance is not None else self._config.default_importance
        mem_id = _generate_memory_id()

        item = MemoryItem(
            memory_id=mem_id,
            memory_type=memory_type,
            scope=scope,
            content=content,
            importance=max(0.0, min(1.0, imp)),
            tags=tags,
            metadata=metadata or {},
            parent_id=parent_id,
            expires_at=expires_at,
            embedding=embedding,
            domain=domain,
            confidence=max(0.0, min(1.0, confidence)),
            sensitivity=sensitivity,
            source=source,
            provenance=provenance,
            retention_policy=retention_policy,
            status=MemoryStatus.ACTIVE,
            version=1,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        try:
            stored = await self._store.create(item)
        except MemoryError:
            raise
        except Exception as exc:
            raise MemoryEngineError(
                f"Failed to store memory: {exc}",
                context={"memory_type": memory_type.value},
            ) from exc

        self._registry.register(stored)

        self._run_hooks("after_store", scope)

        self._publish_event(
            MemoryCreated(
                memory_id=mem_id,
                memory_type=memory_type,
                scope=scope,
                importance=item.importance,
                tags=item.tags,
            )
        )

        self._log.info(
            "engine.memory_created",
            memory_id=mem_id,
            memory_type=memory_type.value,
            scope=scope.scope_key(),
        )
        return stored

    async def get_memory(
        self,
        memory_id: str,
        scope: MemoryScope,
    ) -> MemoryItem | None:
        """Retrieve a memory item by ID.

        Args:
            memory_id: The memory identifier.
            scope: The memory scope.

        Returns:
            The MemoryItem, or None if not found.
        """
        if self._authorize_fn:
            self._authorize_fn("get_memory", scope)

        scoped_id = ScopedMemoryId(memory_id=memory_id, scope=scope)
        item = await self._store.read(scoped_id)

        if item is not None and item.status == MemoryStatus.EXPIRED:
            self._publish_event(
                MemoryExpired(
                    memory_id=memory_id,
                    scope=scope,
                    memory_type=item.memory_type,
                )
            )
            return item

        if item is not None:
            updated = item.model_copy(
                update={
                    "access_count": item.access_count + 1,
                    "accessed_at": utc_now(),
                }
            )
            try:
                await self._store.update(updated)
                self._registry.register(updated)
            except Exception:
                self._log.warning("engine.access_update_failed", memory_id=memory_id)

            self._publish_event(
                MemoryRetrieved(
                    memory_id=memory_id,
                    scope=scope,
                )
            )

        return item

    async def update_memory(
        self,
        memory_id: str,
        scope: MemoryScope,
        *,
        content: str | None = None,
        importance: float | None = None,
        tags: tuple[str, ...] | None = None,
        metadata: dict[str, Any] | None = None,
        status: MemoryStatus | None = None,
    ) -> MemoryItem:
        """Update an existing memory item.

        Args:
            memory_id: The memory identifier.
            scope: The memory scope.
            content: Optional new content.
            importance: Optional new importance.
            tags: Optional new tags.
            metadata: Optional new metadata.
            status: Optional new status.

        Returns:
            The updated MemoryItem.

        Raises:
            MemoryNotFoundError: If the item does not exist.
        """
        if self._authorize_fn:
            self._authorize_fn("update_memory", scope)

        scoped_id = ScopedMemoryId(memory_id=memory_id, scope=scope)
        existing = await self._store.read(scoped_id)
        if existing is None:
            raise MemoryNotFoundError(
                f"Memory {memory_id} not found in scope {scope.scope_key()}",
            )

        changes: list[str] = []
        updates: dict[str, Any] = {
            "updated_at": utc_now(),
            "version": existing.version + 1,
        }
        if content is not None:
            updates["content"] = content
            changes.append("content")
        if importance is not None:
            updates["importance"] = importance
            changes.append("importance")
        if tags is not None:
            updates["tags"] = tags
            changes.append("tags")
        if metadata is not None:
            merged = dict(existing.metadata)
            merged.update(metadata)
            updates["metadata"] = merged
            changes.append("metadata")
        if status is not None:
            updates["status"] = status
            changes.append("status")

        updated = existing.model_copy(update=updates)

        try:
            result = await self._store.update(updated)
        except MemoryError:
            raise
        except Exception as exc:
            raise MemoryEngineError(
                f"Failed to update memory: {exc}",
            ) from exc

        self._registry.register(result)

        self._publish_event(
            MemoryUpdated(
                memory_id=memory_id,
                scope=scope,
                version=result.version,
                changes=tuple(changes),
            )
        )

        self._log.info("engine.memory_updated", memory_id=memory_id, changes=changes)
        return result

    async def delete_memory(
        self,
        memory_id: str,
        scope: MemoryScope,
        reason: str = "",
    ) -> bool:
        """Delete a memory item.

        Args:
            memory_id: The memory identifier.
            scope: The memory scope.
            reason: Optional deletion reason.

        Returns:
            True if the item was deleted.
        """
        if self._authorize_fn:
            self._authorize_fn("delete_memory", scope)

        scoped_id = ScopedMemoryId(memory_id=memory_id, scope=scope)

        self._run_hooks("before_delete", scope)

        result = await self._store.delete(scoped_id)
        self._registry.unregister(scoped_id)

        self._run_hooks("after_delete", scope)

        if result:
            self._publish_event(
                MemoryDeleted(
                    memory_id=memory_id,
                    scope=scope,
                    reason=reason,
                )
            )
            self._log.info("engine.memory_deleted", memory_id=memory_id, reason=reason)

        return result

    async def search_memories(
        self,
        query: MemoryQuery,
    ) -> MemoryResult:
        """Search for memories matching the query.

        Args:
            query: The search query parameters.

        Returns:
            A MemoryResult with matched items.
        """
        t0 = time.monotonic()
        try:
            result = await self._retrieval.search(query)
            duration = (time.monotonic() - t0) * 1000

            self._publish_event(
                MemorySearchExecuted(
                    query=query.query,
                    filters={
                        "memory_types": [t.value for t in query.memory_types],
                        "tags": query.tags,
                    },
                    result_count=result.total_count,
                    duration_ms=duration,
                )
            )
            return result
        except Exception as exc:
            raise MemoryEngineError(
                f"Search failed: {exc}",
                context={"query": query.query},
            ) from exc

    async def retrieve_by_type(
        self,
        memory_type: MemoryType,
        scope: MemoryScope,
        limit: int = 10,
    ) -> list[MemoryItem]:
        """Retrieve memories of a specific type within a scope.

        Args:
            memory_type: The memory type to filter by.
            scope: The scope to search within.
            limit: Maximum number of results.

        Returns:
            A list of memory items.
        """
        if self._authorize_fn:
            self._authorize_fn("retrieve", scope)
        return await self._retrieval.retrieve_by_type(memory_type.value, scope, limit)

    async def retrieve_by_tags(
        self,
        tags: list[str],
        scope: MemoryScope,
        limit: int = 10,
    ) -> list[MemoryItem]:
        """Retrieve memories with specific tags within a scope.

        Args:
            tags: The tags to filter by.
            scope: The scope to search within.
            limit: Maximum number of results.

        Returns:
            A list of memory items.
        """
        if self._authorize_fn:
            self._authorize_fn("retrieve", scope)
        return await self._retrieval.retrieve_by_tags(tags, scope, limit)

    async def clear_scope(self, scope: MemoryScope) -> int:
        """Clear all memory items within a scope.

        Args:
            scope: The scope to clear.

        Returns:
            The number of items cleared.
        """
        if self._authorize_fn:
            self._authorize_fn("clear_scope", scope)

        count = await self._store.clear_scope(scope)
        registry_items = self._registry.list_by_scope(scope)
        for item in registry_items:
            scoped_id = ScopedMemoryId(memory_id=item.memory_id, scope=scope)
            self._registry.unregister(scoped_id)

        self._log.info("engine.scope_cleared", scope=scope.scope_key(), count=count)
        return count

    async def consolidate(
        self,
        memory_type: MemoryType = MemoryType.EPISODIC,
        scope: MemoryScope | None = None,
    ) -> ConsolidationReport:
        """Run memory consolidation for a given type and scope.

        Args:
            memory_type: The memory type to consolidate.
            scope: Optional scope filter.

        Returns:
            A ConsolidationReport with results.
        """
        scope_filter = scope or MemoryScope(tenant_id="*")
        items = await self._store.list_by_scope(
            scope_filter,
            memory_type=memory_type.value,
            status="active",
            limit=1000,
        )
        if self._config.enable_consolidation and items:
            report = await self._consolidation.consolidate_episodic_to_semantic(items)
            if report.source_count > 0:
                self._publish_event(
                    MemoryConsolidated(
                        source_ids=tuple(m.memory_id for m in items[: report.source_count]),
                        consolidated_count=report.consolidated_count,
                    )
                )
            return report
        return ConsolidationReport()

    async def expire_memory(
        self,
        memory_id: str,
        scope: MemoryScope,
    ) -> bool:
        """Expire a specific memory item.

        Args:
            memory_id: The memory identifier.
            scope: The memory scope.

        Returns:
            True if the item was expired.
        """
        scoped_id = ScopedMemoryId(memory_id=memory_id, scope=scope)
        result = await self._expiration.expire_memory(scoped_id)
        if result:
            self._publish_event(
                MemoryExpired(
                    memory_id=memory_id,
                    scope=scope,
                    memory_type=MemoryType.LONG_TERM,
                )
            )
        return result

    async def archive_memory(
        self,
        memory_id: str,
        scope: MemoryScope,
    ) -> bool:
        """Archive a specific memory item.

        Args:
            memory_id: The memory identifier.
            scope: The memory scope.

        Returns:
            True if the item was archived.
        """
        scoped_id = ScopedMemoryId(memory_id=memory_id, scope=scope)
        result = await self._expiration.archive_memory(scoped_id)
        if result:
            self._publish_event(
                MemoryArchived(
                    memory_id=memory_id,
                    scope=scope,
                )
            )
        return result

    async def run_expiration_cycle(self) -> int:
        """Run the expiration cycle for all expired memories.

        Returns:
            The number of items expired.
        """
        count = await self._expiration.run_expiration_cycle()
        if count:
            self._log.info("engine.expiration_cycle", expired=count)
        return count

    async def summarize(
        self,
        memory_ids: list[str],
        scope: MemoryScope,
        max_length: int = 500,
    ) -> str | None:
        """Summarize a list of memories.

        Args:
            memory_ids: The memory IDs to summarize.
            scope: The scope of the memories.
            max_length: Maximum summary length.

        Returns:
            The summary text, or None if no summarizer is configured.
        """
        if self._summarizer is None:
            self._log.warning("engine.summarize.no_summarizer")
            return None

        memories: list[MemoryItem] = []
        for mem_id in memory_ids:
            scoped_id = ScopedMemoryId(memory_id=mem_id, scope=scope)
            item = await self._store.read(scoped_id)
            if item is not None:
                memories.append(item)

        if not memories:
            return None

        summary = await self._summarizer.summarize(memories, max_length)

        self._publish_event(
            MemorySummarized(
                memory_id=",".join(memory_ids),
                scope=scope,
            )
        )
        return summary

    async def health(self) -> dict[str, Any]:
        """Return health status for this engine.

        Returns:
            A dict with health information.
        """
        registry_health = await self._registry.health()
        return {
            "status": "healthy",
            "items": registry_health.get("items", 0),
            "relations": registry_health.get("relations", 0),
        }

    def on(
        self,
        event_type: type[MemoryEngineEvent],
        _handler: Any,
    ) -> None:
        """Register an event handler (stub for compatibility).

        Args:
            event_type: The event type to handle.
        """
        self._log.debug("engine.on", event_type=event_type.__name__)

    def _publish_event(self, event: object) -> None:
        """Publish a domain event.

        Args:
            event: The event to publish.
        """
        if self._event_publisher is not None:
            try:
                self._event_publisher(event)
            except Exception:
                self._log.warning("engine.event_publish_failed")

    def _run_hooks(self, hook_name: str, scope: MemoryScope) -> None:
        """Run lifecycle hooks for the given hook point.

        Args:
            hook_name: The hook point name.
            scope: The scope for context.
        """
        hooks = self._hooks.get(hook_name, [])
        for hook in hooks:
            try:
                hook(scope)
            except Exception:
                self._log.warning("engine.hook_failed", hook=hook_name)


def _generate_memory_id() -> str:
    """Generate a unique memory identifier.

    Returns:
        A unique string identifier.
    """
    return f"mem_{uuid.uuid4().hex[:16]}"


__all__ = ["MemoryEngine"]
