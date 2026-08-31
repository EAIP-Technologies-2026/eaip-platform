"""Memory Engine protocols — abstract interfaces for stores, indexers, retrievers, summarizers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from eaip.memory.models import (
    MemoryItem,
    MemoryQuery,
    MemoryResult,
    MemoryScope,
    MemorySearchResult,
    ScopedMemoryId,
)


@runtime_checkable
class MemoryStore(Protocol):
    """Protocol for persistent memory storage backends.

    Implementations can be in-memory, database-backed, or vector-store-backed.
    """

    async def create(self, item: MemoryItem) -> MemoryItem:
        """Store a new memory item.

        Args:
            item: The memory item to store.

        Returns:
            The stored memory item.

        Raises:
            MemoryStoreError: If the storage operation fails.
        """
        ...

    async def read(self, scoped_id: ScopedMemoryId) -> MemoryItem | None:
        """Read a memory item by its scoped identifier.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            The memory item, or None if not found.
        """
        ...

    async def update(self, item: MemoryItem) -> MemoryItem:
        """Update an existing memory item.

        Args:
            item: The updated memory item.

        Returns:
            The stored memory item.

        Raises:
            MemoryNotFoundError: If the item does not exist.
        """
        ...

    async def delete(self, scoped_id: ScopedMemoryId) -> bool:
        """Delete a memory item.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            True if the item was deleted, False if not found.
        """
        ...

    async def archive(self, scoped_id: ScopedMemoryId) -> bool:
        """Archive a memory item without deleting it.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            True if the item was archived, False if not found.
        """
        ...

    async def restore(self, scoped_id: ScopedMemoryId) -> bool:
        """Restore an archived or expired memory item to active status.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            True if the item was restored, False if not found.
        """
        ...

    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """Search for memory items matching the query.

        Args:
            query: The search query.

        Returns:
            A list of matching search results.
        """
        ...

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
        ...

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
        ...

    async def expire_before(self, before: float, batch_size: int = 100) -> list[str]:
        """Find memory items that expire before the given timestamp.

        Args:
            before: Unix timestamp threshold.
            batch_size: Maximum items to return.

        Returns:
            A list of fully qualified memory IDs that have expired.
        """
        ...

    async def delete_many(self, fq_ids: list[str]) -> int:
        """Delete multiple memory items by their fully qualified IDs.

        Args:
            fq_ids: Fully qualified memory IDs to delete.

        Returns:
            The number of items deleted.
        """
        ...

    async def clear_scope(self, scope: MemoryScope) -> int:
        """Clear all memory items within a scope.

        Args:
            scope: The scope to clear.

        Returns:
            The number of items cleared.
        """
        ...


@runtime_checkable
class MemoryIndexer(Protocol):
    """Protocol for indexing memory items for search."""

    async def index(self, item: MemoryItem) -> None:
        """Index a memory item.

        Args:
            item: The memory item to index.
        """
        ...

    async def remove(self, scoped_id: ScopedMemoryId) -> None:
        """Remove a memory item from the index.

        Args:
            scoped_id: The scoped memory identifier.
        """
        ...

    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """Search the index for matching items.

        Args:
            query: The search query.

        Returns:
            A list of matching search results.
        """
        ...

    async def clear(self) -> None:
        """Clear the entire index."""
        ...


@runtime_checkable
class MemoryRetriever(Protocol):
    """Protocol for retrieving memories by various strategies."""

    async def retrieve_by_id(self, scoped_id: ScopedMemoryId) -> MemoryItem | None:
        """Retrieve a memory by its scoped identifier.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            The memory item, or None if not found.
        """
        ...

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
        ...

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
        ...

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
        ...

    async def search(self, query: MemoryQuery) -> MemoryResult:
        """Search for memories matching the query.

        Args:
            query: The search query.

        Returns:
            A MemoryResult with matched items.
        """
        ...


@runtime_checkable
class MemorySummarizer(Protocol):
    """Protocol for summarizing memory content."""

    async def summarize(
        self,
        memories: list[MemoryItem],
        max_length: int = 500,
    ) -> str:
        """Summarize a list of memory items into condensed text.

        Args:
            memories: The memory items to summarize.
            max_length: Maximum summary length in characters.

        Returns:
            The generated summary text.
        """
        ...


@runtime_checkable
class MemoryProvider(Protocol):
    """Combined protocol for a full memory backend implementation.

    A MemoryProvider must satisfy MemoryStore, MemoryIndexer,
    and MemoryRetriever simultaneously.
    """

    name: str

    async def create(self, item: MemoryItem) -> MemoryItem:
        """Store a new memory item."""
        ...

    async def read(self, scoped_id: ScopedMemoryId) -> MemoryItem | None:
        """Read a memory item."""
        ...

    async def update(self, item: MemoryItem) -> MemoryItem:
        """Update a memory item."""
        ...

    async def delete(self, scoped_id: ScopedMemoryId) -> bool:
        """Delete a memory item."""
        ...

    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """Search for memories."""
        ...

    async def index(self, item: MemoryItem) -> None:
        """Index a memory item."""
        ...

    async def remove_index(self, scoped_id: ScopedMemoryId) -> None:
        """Remove from index."""
        ...

    async def list_by_scope(
        self,
        scope: MemoryScope,
        memory_type: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[MemoryItem]:
        """List items by scope."""
        ...

    async def count_by_scope(
        self,
        scope: MemoryScope,
        memory_type: str | None = None,
        status: str | None = None,
    ) -> int:
        """Count items by scope."""
        ...

    async def retrieve_by_id(self, scoped_id: ScopedMemoryId) -> MemoryItem | None:
        """Retrieve by ID."""
        ...

    async def retrieve_by_type(
        self,
        memory_type: str,
        scope: MemoryScope,
        limit: int = 10,
    ) -> list[MemoryItem]:
        """Retrieve by type."""
        ...

    async def retrieve_by_tags(
        self,
        tags: list[str],
        scope: MemoryScope,
        limit: int = 10,
    ) -> list[MemoryItem]:
        """Retrieve by tags."""
        ...

    async def delete_many(self, fq_ids: list[str]) -> int:
        """Delete many items."""
        ...

    async def clear_scope(self, scope: MemoryScope) -> int:
        """Clear a scope."""
        ...

    async def clear_index(self) -> None:
        """Clear the index."""
        ...


MemoryHook = Callable[[MemoryScope], None]
"""Type alias for memory lifecycle hooks.

Used by the plugin extensibility system to allow plugins to hook into
memory operations before and after they occur.
"""


__all__ = [
    "MemoryHook",
    "MemoryIndexer",
    "MemoryProvider",
    "MemoryRetriever",
    "MemoryStore",
    "MemorySummarizer",
]
