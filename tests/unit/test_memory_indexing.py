"""Tests for memory indexing strategies and indexers."""

from __future__ import annotations

import pytest

from eaip.memory.indexing import (
    AlwaysIndexStrategy,
    CompositeIndexer,
    ContentIndexer,
    MetadataIndexer,
    NeverIndexStrategy,
    TagIndexer,
)
from eaip.memory.models import MemoryItem, MemoryQuery, MemoryScope, MemoryType, ScopedMemoryId


@pytest.fixture
def scope() -> MemoryScope:
    return MemoryScope(tenant_id="t1", user_id="u1")


@pytest.fixture
def item(scope: MemoryScope) -> MemoryItem:
    return MemoryItem(
        memory_id="m1",
        memory_type=MemoryType.WORKING,
        scope=scope,
        content="the quick brown fox jumps over the lazy dog",
        tags=("animal", "test"),
        importance=0.9,
    )


class TestAlwaysIndexStrategy:
    def test_always_indexes(self, item: MemoryItem) -> None:
        strategy = AlwaysIndexStrategy()
        assert strategy.should_index(item) is True


class TestNeverIndexStrategy:
    def test_never_indexes(self, item: MemoryItem) -> None:
        strategy = NeverIndexStrategy()
        assert strategy.should_index(item) is False


class TestContentIndexer:
    @pytest.mark.asyncio
    async def test_index_and_search(self, scope: MemoryScope, item: MemoryItem) -> None:
        indexer = ContentIndexer()
        await indexer.index(item)

        query = MemoryQuery(query="quick fox")
        results = await indexer.search(query)
        assert len(results) == 1
        assert results[0].memory.memory_id == "m1"

    @pytest.mark.asyncio
    async def test_search_no_match(self, scope: MemoryScope, item: MemoryItem) -> None:
        indexer = ContentIndexer()
        await indexer.index(item)

        query = MemoryQuery(query="nonexistent")
        results = await indexer.search(query)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_empty_query(self, scope: MemoryScope, item: MemoryItem) -> None:
        indexer = ContentIndexer()
        await indexer.index(item)

        query = MemoryQuery(query="")
        results = await indexer.search(query)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_remove(self, scope: MemoryScope, item: MemoryItem) -> None:
        indexer = ContentIndexer()
        await indexer.index(item)
        await indexer.remove(ScopedMemoryId(memory_id="m1", scope=scope))

        query = MemoryQuery(query="quick")
        results = await indexer.search(query)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_clear(self, scope: MemoryScope, item: MemoryItem) -> None:
        indexer = ContentIndexer()
        await indexer.index(item)
        await indexer.clear()

        query = MemoryQuery(query="quick")
        results = await indexer.search(query)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_index_multiple_items(self, scope: MemoryScope) -> None:
        indexer = ContentIndexer()
        item1 = MemoryItem(
            memory_id="a", memory_type=MemoryType.WORKING, scope=scope, content="hello world"
        )
        item2 = MemoryItem(
            memory_id="b", memory_type=MemoryType.WORKING, scope=scope, content="hello there"
        )
        await indexer.index(item1)
        await indexer.index(item2)

        query = MemoryQuery(query="hello")
        results = await indexer.search(query)
        assert len(results) == 2

        query = MemoryQuery(query="world")
        results = await indexer.search(query)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_with_filters(self, scope: MemoryScope) -> None:
        indexer = ContentIndexer()
        item1 = MemoryItem(
            memory_id="a",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="important data",
            importance=0.9,
        )
        item2 = MemoryItem(
            memory_id="b",
            memory_type=MemoryType.SESSION,
            scope=scope,
            content="important data",
            importance=0.3,
        )
        await indexer.index(item1)
        await indexer.index(item2)

        query = MemoryQuery(
            query="important", memory_types=(MemoryType.WORKING,), importance_min=0.5
        )
        results = await indexer.search(query)
        assert len(results) == 1
        assert results[0].memory.memory_id == "a"


class TestTagIndexer:
    @pytest.mark.asyncio
    async def test_index_and_search(self, scope: MemoryScope, item: MemoryItem) -> None:
        indexer = TagIndexer()
        await indexer.index(item)

        query = MemoryQuery(query="", tags=("animal",))
        results = await indexer.search(query)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_no_tags_in_query(self, scope: MemoryScope, item: MemoryItem) -> None:
        indexer = TagIndexer()
        await indexer.index(item)

        query = MemoryQuery(query="")
        results = await indexer.search(query)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_tag_no_match(self, scope: MemoryScope, item: MemoryItem) -> None:
        indexer = TagIndexer()
        await indexer.index(item)

        query = MemoryQuery(query="", tags=("nonexistent",))
        results = await indexer.search(query)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_remove(self, scope: MemoryScope, item: MemoryItem) -> None:
        indexer = TagIndexer()
        await indexer.index(item)
        await indexer.remove(ScopedMemoryId(memory_id="m1", scope=scope))

        query = MemoryQuery(query="", tags=("animal",))
        results = await indexer.search(query)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_clear(self, scope: MemoryScope, item: MemoryItem) -> None:
        indexer = TagIndexer()
        await indexer.index(item)
        await indexer.clear()

        query = MemoryQuery(query="", tags=("animal",))
        results = await indexer.search(query)
        assert len(results) == 0


class TestMetadataIndexer:
    @pytest.mark.asyncio
    async def test_index_and_search(self, scope: MemoryScope, item: MemoryItem) -> None:
        indexer = MetadataIndexer()
        await indexer.index(item)

        query = MemoryQuery(query="")
        results = await indexer.search(query)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_remove(self, scope: MemoryScope, item: MemoryItem) -> None:
        indexer = MetadataIndexer()
        await indexer.index(item)
        await indexer.remove(ScopedMemoryId(memory_id="m1", scope=scope))

    @pytest.mark.asyncio
    async def test_clear(self, scope: MemoryScope, item: MemoryItem) -> None:
        indexer = MetadataIndexer()
        await indexer.index(item)
        await indexer.clear()


class TestCompositeIndexer:
    @pytest.mark.asyncio
    async def test_index_and_search_across_sub_indexers(
        self, scope: MemoryScope, item: MemoryItem
    ) -> None:
        content = ContentIndexer()
        tag = TagIndexer()
        composite = CompositeIndexer([content, tag])
        await composite.index(item)

        query = MemoryQuery(query="quick", tags=("animal",))
        results = await composite.search(query)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_remove_from_all(self, scope: MemoryScope, item: MemoryItem) -> None:
        content = ContentIndexer()
        tag = TagIndexer()
        composite = CompositeIndexer([content, tag])
        await composite.index(item)
        await composite.remove(ScopedMemoryId(memory_id="m1", scope=scope))

        query = MemoryQuery(query="quick")
        results = await composite.search(query)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_clear_all(self, scope: MemoryScope, item: MemoryItem) -> None:
        content = ContentIndexer()
        tag = TagIndexer()
        composite = CompositeIndexer([content, tag])
        await composite.index(item)
        await composite.clear()

        query = MemoryQuery(query="quick")
        results = await composite.search(query)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_empty_indexers(self, scope: MemoryScope, item: MemoryItem) -> None:
        composite = CompositeIndexer([])
        await composite.index(item)
        query = MemoryQuery(query="quick")
        results = await composite.search(query)
        assert len(results) == 0
