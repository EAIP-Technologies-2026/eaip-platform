"""Memory indexing — strategies for building searchable indexes over memories."""

from __future__ import annotations

import re
from typing import Any, Protocol

from eaip.logging.context import get_logger
from eaip.memory.models import (
    MemoryItem,
    MemoryQuery,
    MemorySearchResult,
    ScopedMemoryId,
)


class IndexingStrategy(Protocol):
    """Protocol for memory indexing strategies.

    Determines whether a memory item should be indexed based on
    its properties and the current state.
    """

    def should_index(self, item: MemoryItem) -> bool:
        """Determine if a memory item should be indexed.

        Args:
            item: The memory item to evaluate.

        Returns:
            True if the item should be indexed.
        """
        ...


class AlwaysIndexStrategy:
    """Indexing strategy that indexes all memory items."""

    def should_index(self, _item: MemoryItem) -> bool:
        """Always return True.

        Returns:
            Always True.
        """
        return True


class NeverIndexStrategy:
    """Indexing strategy that never indexes."""

    def should_index(self, _item: MemoryItem) -> bool:
        """Always return False.

        Returns:
            Always False.
        """
        return False


class ContentIndexer:
    """Indexes memory content for text search.

    Maintains an in-memory inverted index mapping terms to memory
    items for fast text-based retrieval.
    """

    def __init__(self) -> None:
        """Initialize the content indexer."""
        self._index: dict[str, set[str]] = {}
        self._items: dict[str, MemoryItem] = {}
        self._log = get_logger("eaip.memory.indexing.content")

    async def index(self, item: MemoryItem) -> None:
        """Index a memory item by its content and tags.

        Args:
            item: The memory item to index.
        """
        fq_id = ScopedMemoryId(memory_id=item.memory_id, scope=item.scope).fully_qualified()
        await self.remove(ScopedMemoryId(memory_id=item.memory_id, scope=item.scope))
        self._items[fq_id] = item
        terms = self._tokenize(item.content)
        for tag in item.tags:
            terms.add(tag.lower())
        for term in terms:
            if term not in self._index:
                self._index[term] = set()
            self._index[term].add(fq_id)
        self._log.debug("indexer.indexed", fq_id=fq_id, terms=len(terms))

    async def remove(self, scoped_id: ScopedMemoryId) -> None:
        """Remove a memory item from the index.

        Args:
            scoped_id: The scoped memory identifier.
        """
        fq_id = scoped_id.fully_qualified()
        self._items.pop(fq_id, None)
        for term_set in self._index.values():
            term_set.discard(fq_id)
        self._log.debug("indexer.removed", fq_id=fq_id)

    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """Search the index for items matching the query.

        Args:
            query: The search query.

        Returns:
            A list of matching search results.
        """
        if not query.query:
            return []

        terms = self._tokenize(query.query)
        if not terms:
            return []

        matched_fq_ids: set[str] | None = None
        for term in terms:
            if term in self._index:
                if matched_fq_ids is None:
                    matched_fq_ids = set(self._index[term])
                else:
                    matched_fq_ids &= self._index[term]

        if matched_fq_ids is None:
            return []

        results: list[MemorySearchResult] = []
        for fq_id in matched_fq_ids:
            item = self._items.get(fq_id)
            if item is None:
                continue
            if not _matches_query_filters(item, query):
                continue
            score = self._compute_score(item, query)
            if score >= query.score_threshold:
                results.append(MemorySearchResult(memory=item, score=score))

        sorted_results = sorted(results, key=lambda r: r.score, reverse=True)
        return sorted_results[: query.limit]

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize text into lowercase terms.

        Args:
            text: The text to tokenize.

        Returns:
            A set of lowercase terms.
        """
        return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))

    def _compute_score(self, item: MemoryItem, query: MemoryQuery) -> float:
        """Compute relevance score for an item against the query.

        Args:
            item: The memory item.
            query: The search query.

        Returns:
            A relevance score between 0.0 and 1.0.
        """
        score = 0.5
        q = query.query.lower()
        content_lower = item.content.lower()
        if q in content_lower:
            score += 0.3
        matching_tags = sum(1 for t in item.tags if t.lower() in q)
        if matching_tags:
            score += 0.2 * matching_tags / max(len(item.tags), 1)
        score += item.importance * 0.1
        return min(score, 1.0)

    async def clear(self) -> None:
        """Clear the entire index."""
        self._index.clear()
        self._items.clear()
        self._log.debug("indexer.cleared")


class TagIndexer:
    """Indexes memories by their tags for tag-based retrieval."""

    def __init__(self) -> None:
        """Initialize the tag indexer."""
        self._tag_index: dict[str, set[str]] = {}
        self._items: dict[str, MemoryItem] = {}
        self._log = get_logger("eaip.memory.indexing.tag")

    async def index(self, item: MemoryItem) -> None:
        """Index a memory item by its tags.

        Args:
            item: The memory item to index.
        """
        fq_id = ScopedMemoryId(memory_id=item.memory_id, scope=item.scope).fully_qualified()
        await self.remove(ScopedMemoryId(memory_id=item.memory_id, scope=item.scope))
        self._items[fq_id] = item
        for tag in item.tags:
            lower_tag = tag.lower()
            if lower_tag not in self._tag_index:
                self._tag_index[lower_tag] = set()
            self._tag_index[lower_tag].add(fq_id)

    async def remove(self, scoped_id: ScopedMemoryId) -> None:
        """Remove a memory item from the tag index.

        Args:
            scoped_id: The scoped memory identifier.
        """
        fq_id = scoped_id.fully_qualified()
        self._items.pop(fq_id, None)
        for tag_set in self._tag_index.values():
            tag_set.discard(fq_id)

    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """Search by tags.

        Args:
            query: The search query with tags.

        Returns:
            A list of matching search results.
        """
        if not query.tags:
            return []

        matched: set[str] | None = None
        for tag in query.tags:
            lower_tag = tag.lower()
            if lower_tag in self._tag_index:
                if matched is None:
                    matched = set(self._tag_index[lower_tag])
                else:
                    matched &= self._tag_index[lower_tag]

        if matched is None:
            return []

        results: list[MemorySearchResult] = []
        for fq_id in matched:
            item = self._items.get(fq_id)
            if item is not None and _matches_query_filters(item, query):
                results.append(MemorySearchResult(memory=item, score=1.0))
        return results[: query.limit]

    async def clear(self) -> None:
        """Clear the tag index."""
        self._tag_index.clear()
        self._items.clear()


class MetadataIndexer:
    """Indexes memories by metadata fields for filtered retrieval."""

    def __init__(self) -> None:
        """Initialize the metadata indexer."""
        self._items: dict[str, MemoryItem] = {}

    async def index(self, item: MemoryItem) -> None:
        """Index a memory item.

        Args:
            item: The memory item to index.
        """
        fq_id = ScopedMemoryId(memory_id=item.memory_id, scope=item.scope).fully_qualified()
        self._items[fq_id] = item

    async def remove(self, scoped_id: ScopedMemoryId) -> None:
        """Remove a memory item.

        Args:
            scoped_id: The scoped memory identifier.
        """
        self._items.pop(scoped_id.fully_qualified(), None)

    async def search(self, _query: MemoryQuery) -> list[MemorySearchResult]:
        """Search by metadata filters.

        Returns:
            A list of matching search results.
        """
        return []

    async def clear(self) -> None:
        """Clear the metadata index."""
        self._items.clear()


class CompositeIndexer:
    """Composite indexer that delegates to multiple sub-indexers.

    Runs all sub-indexers in sequence for index/remove operations
    and merges results from sub-indexers for search.
    """

    def __init__(self, indexers: list[Any]) -> None:
        """Initialize the composite indexer.

        Args:
            indexers: List of indexer instances to delegate to.
        """
        self._indexers = indexers
        self._log = get_logger("eaip.memory.indexing.composite")

    async def index(self, item: MemoryItem) -> None:
        """Index a memory item across all sub-indexers.

        Args:
            item: The memory item to index.
        """
        for idx in self._indexers:
            try:
                await idx.index(item)
            except Exception as exc:
                self._log.warning(
                    "composite.index_failed",
                    indexer=type(idx).__name__,
                    error=str(exc),
                )

    async def remove(self, scoped_id: ScopedMemoryId) -> None:
        """Remove from all sub-indexers.

        Args:
            scoped_id: The scoped memory identifier.
        """
        for idx in self._indexers:
            try:
                await idx.remove(scoped_id)
            except Exception:
                self._log.warning("composite.remove_failed", indexer=type(idx).__name__)

    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """Search across all sub-indexers, merging results.

        Args:
            query: The search query.

        Returns:
            A merged list of search results.
        """
        all_results: dict[str, MemorySearchResult] = {}
        for idx in self._indexers:
            try:
                results = await idx.search(query)
                for r in results:
                    fq = ScopedMemoryId(
                        memory_id=r.memory.memory_id,
                        scope=r.memory.scope,
                    ).fully_qualified()
                    if fq not in all_results or r.score > all_results[fq].score:
                        all_results[fq] = r
            except Exception:
                self._log.warning("composite.search_failed", indexer=type(idx).__name__)

        sorted_items = sorted(all_results.values(), key=lambda r: r.score, reverse=True)
        return sorted_items[: query.limit]

    async def clear(self) -> None:
        """Clear all sub-indexers."""
        for idx in self._indexers:
            try:
                await idx.clear()
            except Exception:
                self._log.warning("composite.clear_failed", indexer=type(idx).__name__)


def _matches_query_filters(item: MemoryItem, query: MemoryQuery) -> bool:
    if query.memory_types and item.memory_type not in query.memory_types:
        return False
    if query.scopes and item.scope not in query.scopes:
        return False
    if query.tags and not any(tag in item.tags for tag in query.tags):
        return False
    if query.status is not None and item.status != query.status:
        return False
    return query.importance_min <= item.importance <= query.importance_max


__all__ = [
    "AlwaysIndexStrategy",
    "CompositeIndexer",
    "ContentIndexer",
    "IndexingStrategy",
    "MetadataIndexer",
    "NeverIndexStrategy",
    "TagIndexer",
]
