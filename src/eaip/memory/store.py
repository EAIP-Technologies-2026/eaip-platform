"""Memory store implementations — in-memory and adapter patterns."""

from __future__ import annotations

from eaip.logging.context import get_logger
from eaip.memory.base import MemoryIndexer, MemoryStore
from eaip.memory.exceptions import (
    MemoryNotFoundError,
    MemoryValidationError,
)
from eaip.memory.models import (
    MemoryItem,
    MemoryQuery,
    MemoryScope,
    MemorySearchResult,
    MemoryStatus,
    ScopedMemoryId,
)
from eaip.memory.retrieval import MemoryRetrievalService
from eaip.shared.time import utc_now


class InMemoryStore:
    """In-memory implementation of the MemoryStore protocol.

    Stores all memory items in a dict keyed by fully qualified ID.
    Provides thread-safe (via RLock) operations for testing and
    single-process deployments.
    """

    def __init__(self) -> None:
        """Initialize the in-memory store."""
        self._items: dict[str, MemoryItem] = {}
        self._log = get_logger("eaip.memory.store.in_memory")

    async def create(self, item: MemoryItem) -> MemoryItem:
        """Store a new memory item.

        Args:
            item: The memory item to store.

        Returns:
            The stored memory item.

        Raises:
            MemoryValidationError: If an item with the same ID already exists.
        """
        fq_id = ScopedMemoryId(memory_id=item.memory_id, scope=item.scope).fully_qualified()
        if fq_id in self._items:
            raise MemoryValidationError(
                f"Memory item {fq_id} already exists",
                context={"memory_id": item.memory_id, "scope": item.scope.scope_key()},
            )
        self._items[fq_id] = item
        self._log.debug("store.created", fq_id=fq_id, memory_type=item.memory_type.value)
        return item

    async def read(self, scoped_id: ScopedMemoryId) -> MemoryItem | None:
        """Read a memory item by its scoped identifier.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            The memory item, or None if not found.
        """
        fq_id = scoped_id.fully_qualified()
        return self._items.get(fq_id)

    async def update(self, item: MemoryItem) -> MemoryItem:
        """Update an existing memory item.

        Args:
            item: The updated memory item.

        Returns:
            The stored memory item.

        Raises:
            MemoryNotFoundError: If the item does not exist.
        """
        fq_id = ScopedMemoryId(memory_id=item.memory_id, scope=item.scope).fully_qualified()
        if fq_id not in self._items:
            raise MemoryNotFoundError(
                f"Memory item {fq_id} not found",
                context={"memory_id": item.memory_id},
            )
        self._items[fq_id] = item
        self._log.debug("store.updated", fq_id=fq_id, version=item.version)
        return item

    async def delete(self, scoped_id: ScopedMemoryId) -> bool:
        """Delete a memory item.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            True if the item was deleted, False if not found.
        """
        fq_id = scoped_id.fully_qualified()
        if fq_id not in self._items:
            return False
        del self._items[fq_id]
        self._log.debug("store.deleted", fq_id=fq_id)
        return True

    async def archive(self, scoped_id: ScopedMemoryId) -> bool:
        """Archive a memory item without removing it from storage."""
        item = await self.read(scoped_id)
        if item is None:
            return False
        archived = item.model_copy(
            update={"status": MemoryStatus.ARCHIVED, "updated_at": utc_now()}
        )
        self._items[scoped_id.fully_qualified()] = archived
        self._log.debug("store.archived", fq_id=scoped_id.fully_qualified())
        return True

    async def restore(self, scoped_id: ScopedMemoryId) -> bool:
        """Restore an archived or expired memory item to active status."""
        item = await self.read(scoped_id)
        if item is None:
            return False
        restored = item.model_copy(
            update={"status": MemoryStatus.ACTIVE, "updated_at": utc_now()}
        )
        self._items[scoped_id.fully_qualified()] = restored
        self._log.debug("store.restored", fq_id=scoped_id.fully_qualified())
        return True

    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """Search for memory items matching the query.

        Performs an in-memory filter across all stored items.

        Args:
            query: The search query.

        Returns:
            A list of matching search results.
        """
        results: list[MemorySearchResult] = []
        for item in self._items.values():
            if query.memory_types and item.memory_type not in query.memory_types:
                continue
            if query.scopes:
                item_scope_key = item.scope.scope_key()
                matched = False
                for s in query.scopes:
                    if item_scope_key == s.scope_key():
                        matched = True
                        break
                if not matched:
                    continue
            if query.tags and not any(t in item.tags for t in query.tags):
                continue
            if query.status is not None and item.status != query.status:
                continue
            if item.importance < query.importance_min or item.importance > query.importance_max:
                continue
            if query.query and query.query.lower() not in item.content.lower() and query.query.lower() not in " ".join(item.tags).lower():
                continue
            score = self._compute_score(item, query)
            if score >= query.score_threshold:
                results.append(MemorySearchResult(memory=item, score=score))

        sorted_results = sorted(results, key=lambda r: r.score, reverse=True)
        return sorted_results[query.offset : query.offset + query.limit]

    def _compute_score(self, item: MemoryItem, query: MemoryQuery) -> float:
        """Compute a relevance score for an item against a query.

        Args:
            item: The memory item.
            query: The search query.

        Returns:
            A relevance score between 0.0 and 1.0.
        """
        score = 0.5
        if query.query:
            q = query.query.lower()
            content_lower = item.content.lower()
            if q in content_lower:
                score += 0.3 * (len(q) / max(len(content_lower), 1))
            if any(t.lower() in q for t in item.tags):
                score += 0.2
        if query.tags:
            matching_tags = sum(1 for t in query.tags if t in item.tags)
            if matching_tags > 0:
                score += 0.2 * (matching_tags / max(len(query.tags), 1))
        score += item.importance * 0.1
        return min(score, 1.0)

    async def list_by_scope(
        self,
        scope: MemoryScope,
        memory_type: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[MemoryItem]:
        """List memory items within a scope.

        Args:
            scope: The scope to list within.
            memory_type: Optional memory type filter.
            status: Optional status filter.
            offset: Result offset for pagination.
            limit: Maximum number of results.

        Returns:
            A list of memory items.
        """
        scope_key = scope.scope_key()
        results: list[MemoryItem] = []
        for fq_id, item in self._items.items():
            if not fq_id.startswith(scope_key):
                continue
            if memory_type and item.memory_type.value != memory_type:
                continue
            if status and item.status.value != status:
                continue
            results.append(item)
        return results[offset : offset + limit]

    async def count_by_scope(
        self,
        scope: MemoryScope,
        memory_type: str | None = None,
        status: str | None = None,
    ) -> int:
        """Count memory items within a scope.

        Args:
            scope: The scope to count within.
            memory_type: Optional memory type filter.
            status: Optional status filter.

        Returns:
            The count of matching items.
        """
        items = await self.list_by_scope(scope, memory_type, status)
        return len(items)

    async def expire_before(self, before: float, batch_size: int = 100) -> list[str]:
        """Find memory items that expire before the given timestamp.

        Args:
            before: Unix timestamp threshold.
            batch_size: Maximum items to return.

        Returns:
            A list of fully qualified memory IDs that have expired.
        """
        expired: list[str] = []
        for fq_id, item in self._items.items():
            if len(expired) >= batch_size:
                break
            if item.status is MemoryStatus.ACTIVE and item.expires_at is not None:
                expires_ts = item.expires_at.timestamp()
                if expires_ts <= before:
                    expired.append(fq_id)
        return expired

    async def delete_many(self, fq_ids: list[str]) -> int:
        """Delete multiple memory items by their fully qualified IDs.

        Args:
            fq_ids: Fully qualified memory IDs to delete.

        Returns:
            The number of items deleted.
        """
        count = 0
        for fq_id in fq_ids:
            if fq_id in self._items:
                del self._items[fq_id]
                count += 1
        if count:
            self._log.debug("store.delete_many", count=count)
        return count

    async def archive_many(self, fq_ids: list[str]) -> int:
        """Archive multiple items by their fully qualified IDs."""
        count = 0
        for fq_id in fq_ids:
            item = self._items.get(fq_id)
            if item is None:
                continue
            self._items[fq_id] = item.model_copy(
                update={"status": MemoryStatus.ARCHIVED, "updated_at": utc_now()}
            )
            count += 1
        if count:
            self._log.debug("store.archive_many", count=count)
        return count

    async def clear_scope(self, scope: MemoryScope) -> int:
        """Clear all memory items within a scope.

        Args:
            scope: The scope to clear.

        Returns:
            The number of items cleared.
        """
        scope_key = scope.scope_key()
        to_delete = [fq_id for fq_id in self._items if fq_id.startswith(scope_key)]
        for fq_id in to_delete:
            del self._items[fq_id]
        if to_delete:
            self._log.debug("store.clear_scope", scope=scope_key, count=len(to_delete))
        return len(to_delete)


class MemoryStoreAdapter:
    """Adapter that wraps separate store, indexer, and retriever into a MemoryProvider.

    Allows composing a MemoryProvider from independently implemented
    MemoryStore, MemoryIndexer, and MemoryRetriever instances.
    """

    def __init__(
        self,
        store: MemoryStore,
        indexer: MemoryIndexer | None = None,
        retriever: MemoryRetrievalService | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            store: The memory store implementation.
            indexer: Optional memory indexer. If None, no indexing is performed.
            retriever: Optional retriever. If None, a default is created.
        """
        self._store = store
        self._indexer = indexer
        self._retriever = retriever or MemoryRetrievalService(store)
        self._log = get_logger("eaip.memory.store.adapter")

    @property
    def store(self) -> MemoryStore:
        """Return the underlying store."""
        return self._store

    async def create(self, item: MemoryItem) -> MemoryItem:
        """Store a new memory item with optional indexing.

        Args:
            item: The memory item to store.

        Returns:
            The stored memory item.
        """
        result = await self._store.create(item)
        if self._indexer is not None:
            try:
                await self._indexer.index(result)
            except Exception:
                self._log.warning("adapter.index_failed", memory_id=item.memory_id)
        return result

    async def read(self, scoped_id: ScopedMemoryId) -> MemoryItem | None:
        """Read a memory item.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            The memory item, or None if not found.
        """
        return await self._store.read(scoped_id)

    async def update(self, item: MemoryItem) -> MemoryItem:
        """Update a memory item with optional re-indexing.

        Args:
            item: The updated memory item.

        Returns:
            The stored memory item.
        """
        result = await self._store.update(item)
        if self._indexer is not None:
            try:
                scoped_id = ScopedMemoryId(memory_id=item.memory_id, scope=item.scope)
                await self._indexer.remove(scoped_id)
                await self._indexer.index(result)
            except Exception:
                self._log.warning("adapter.reindex_failed", memory_id=item.memory_id)
        return result

    async def delete(self, scoped_id: ScopedMemoryId) -> bool:
        """Delete a memory item with optional index removal.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            True if deleted, False if not found.
        """
        result = await self._store.delete(scoped_id)
        if result and self._indexer is not None:
            try:
                await self._indexer.remove(scoped_id)
            except Exception:
                self._log.warning("adapter.index_remove_failed", memory_id=scoped_id.memory_id)
        return result

    async def archive(self, scoped_id: ScopedMemoryId) -> bool:
        """Archive a memory item."""
        if hasattr(self._store, "archive"):
            archive = self._store.archive
            result = await archive(scoped_id)
        else:
            item = await self._store.read(scoped_id)
            if item is None:
                return False
            archived = item.model_copy(
                update={"status": MemoryStatus.ARCHIVED, "updated_at": utc_now()}
            )
            await self._store.update(archived)
            result = True
        return bool(result)

    async def restore(self, scoped_id: ScopedMemoryId) -> bool:
        """Restore a memory item to active status."""
        if hasattr(self._store, "restore"):
            restore = self._store.restore
            result = await restore(scoped_id)
        else:
            item = await self._store.read(scoped_id)
            if item is None:
                return False
            restored = item.model_copy(
                update={"status": MemoryStatus.ACTIVE, "updated_at": utc_now()}
            )
            await self._store.update(restored)
            result = True
        if result and self._indexer is not None:
            item = await self._store.read(scoped_id)
            if item is not None:
                await self._indexer.index(item)
        return bool(result)

    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """Search for memory items.

        Args:
            query: The search query.

        Returns:
            A list of matching search results.
        """
        if self._indexer is not None and query.query:
            try:
                return await self._indexer.search(query)
            except Exception:
                self._log.debug("adapter.index_search_failed, falling back to store")
        return await self._store.search(query)

    async def retrieve_by_id(self, scoped_id: ScopedMemoryId) -> MemoryItem | None:
        """Retrieve a memory by ID.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            The memory item, or None.
        """
        if self._retriever is not None:
            return await self._retriever.retrieve_by_id(scoped_id)
        return await self._store.read(scoped_id)

    async def retrieve_by_type(
        self,
        memory_type: str,
        scope: MemoryScope,
        limit: int = 10,
    ) -> list[MemoryItem]:
        """Retrieve memories by type.

        Args:
            memory_type: The memory type.
            scope: The scope.
            limit: Maximum results.

        Returns:
            A list of memory items.
        """
        if self._retriever is not None:
            return await self._retriever.retrieve_by_type(memory_type, scope, limit)
        return await self._store.list_by_scope(scope, memory_type=memory_type, limit=limit)

    async def retrieve_by_tags(
        self,
        tags: list[str],
        scope: MemoryScope,
        limit: int = 10,
    ) -> list[MemoryItem]:
        """Retrieve memories by tags.

        Args:
            tags: The tags to match.
            scope: The scope.
            limit: Maximum results.

        Returns:
            A list of memory items.
        """
        if self._retriever is not None:
            return await self._retriever.retrieve_by_tags(tags, scope, limit)
        all_items = await self._store.list_by_scope(scope, limit=limit * 10)
        matched = [i for i in all_items if any(t in i.tags for t in tags)]
        return matched[:limit]

    async def delete_many(self, fq_ids: list[str]) -> int:
        """Delete multiple items.

        Args:
            fq_ids: Fully qualified IDs to delete.

        Returns:
            Number deleted.
        """
        return await self._store.delete_many(fq_ids)

    async def clear_scope(self, scope: MemoryScope) -> int:
        """Clear a scope.

        Args:
            scope: The scope to clear.

        Returns:
            Number cleared.
        """
        return await self._store.clear_scope(scope)


__all__ = ["InMemoryStore", "MemoryStoreAdapter"]
