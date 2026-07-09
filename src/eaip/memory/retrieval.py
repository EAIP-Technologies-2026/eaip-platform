"""MemoryRetrievalService — searching and retrieving memories."""

from __future__ import annotations

import time

from eaip.logging.context import get_logger
from eaip.memory.base import MemoryStore
from eaip.memory.exceptions import MemoryRetrievalError
from eaip.memory.models import (
    MemoryItem,
    MemoryQuery,
    MemoryResult,
    MemoryScope,
    MemorySearchResult,
    ScopedMemoryId,
)


class MemoryRetrievalService:
    """Service for retrieving memories from a store.

    Provides multiple retrieval strategies including by ID, type,
    tags, relations, and free-form search.
    """

    def __init__(self, store: MemoryStore) -> None:
        """Initialize the retrieval service.

        Args:
            store: The memory store to query.
        """
        self._store = store
        self._log = get_logger("eaip.memory.retrieval")

    async def retrieve_by_id(self, scoped_id: ScopedMemoryId) -> MemoryItem | None:
        """Retrieve a single memory by its scoped identifier.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            The memory item, or None if not found.
        """
        return await self._store.read(scoped_id)

    async def retrieve_by_type(
        self,
        memory_type: str,
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
        return await self._store.list_by_scope(
            scope, memory_type=memory_type, status="active", limit=limit
        )

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
        all_items = await self._store.list_by_scope(
            scope, status="active", limit=limit * 10
        )
        matched: list[MemoryItem] = []
        for item in all_items:
            if any(t in item.tags for t in tags):
                matched.append(item)
                if len(matched) >= limit:
                    break
        return matched

    async def retrieve_related(
        self,
        scoped_id: ScopedMemoryId,
        max_depth: int = 1,
        limit: int = 10,
    ) -> list[MemoryItem]:
        """Retrieve memories related to a given memory.

        Args:
            scoped_id: The scoped memory identifier.
            max_depth: Maximum relationship traversal depth.
            limit: Maximum number of results.

        Returns:
            A list of related memory items.
        """
        if max_depth < 1:
            return []

        root = await self._store.read(scoped_id)
        if root is None:
            return []

        results: list[MemoryItem] = []
        seen: set[str] = {scoped_id.memory_id}
        frontier = list(root.related_ids)
        depth = 0

        while frontier and depth < max_depth and len(results) < limit:
            next_frontier: list[str] = []
            for memory_id in frontier:
                if len(results) >= limit or memory_id in seen:
                    continue
                seen.add(memory_id)
                item = await self._store.read(
                    ScopedMemoryId(memory_id=memory_id, scope=scoped_id.scope)
                )
                if item is None:
                    continue
                results.append(item)
                next_frontier.extend(item.related_ids)
            frontier = next_frontier
            depth += 1
        return results

    async def search(self, query: MemoryQuery) -> MemoryResult:
        """Search for memories matching the query.

        Args:
            query: The search query.

        Returns:
            A MemoryResult with matched items.

        Raises:
            MemoryRetrievalError: If the search operation fails.
        """
        t0 = time.monotonic()
        try:
            results = await self._store.search(query)
            total = len(results)
            result_items = tuple(
                MemorySearchResult(memory=r.memory, score=r.score)
                for r in results
            )
            duration = (time.monotonic() - t0) * 1000
            self._log.debug(
                "retrieval.search",
                query=query.query,
                results=total,
                duration_ms=round(duration, 2),
            )
            return MemoryResult(
                query=query.query,
                results=result_items,
                total_count=total,
                duration_ms=duration,
            )
        except MemoryRetrievalError:
            raise
        except Exception as exc:
            raise MemoryRetrievalError(
                f"Search failed: {exc}",
                context={"query": query.query},
            ) from exc


__all__ = ["MemoryRetrievalService"]
