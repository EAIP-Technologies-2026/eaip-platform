"""Tests for MemoryRetrievalService."""

from __future__ import annotations

import pytest

from eaip.memory.models import (
    MemoryItem,
    MemoryQuery,
    MemoryScope,
    MemoryType,
    ScopedMemoryId,
)
from eaip.memory.retrieval import MemoryRetrievalService
from eaip.memory.store import InMemoryStore


@pytest.fixture
def scope() -> MemoryScope:
    return MemoryScope(tenant_id="t1", user_id="u1")


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def retrieval(store: InMemoryStore) -> MemoryRetrievalService:
    return MemoryRetrievalService(store)


@pytest.fixture
async def populated_store(store: InMemoryStore, scope: MemoryScope) -> InMemoryStore:
    items = [
        MemoryItem(
            memory_id="m1",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="first memory",
            tags=("a",),
        ),
        MemoryItem(
            memory_id="m2",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="second memory",
            tags=("b",),
        ),
        MemoryItem(
            memory_id="m3",
            memory_type=MemoryType.SESSION,
            scope=scope,
            content="third memory",
            tags=("a",),
        ),
    ]
    for item in items:
        await store.create(item)
    return store


class TestMemoryRetrievalService:
    @pytest.mark.asyncio
    async def test_retrieve_by_id(
        self, retrieval: MemoryRetrievalService, store: InMemoryStore, scope: MemoryScope
    ) -> None:
        item = MemoryItem(
            memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="hello"
        )
        await store.create(item)
        scoped_id = ScopedMemoryId(memory_id="m1", scope=scope)
        result = await retrieval.retrieve_by_id(scoped_id)
        assert result is not None
        assert result.content == "hello"

    @pytest.mark.asyncio
    async def test_retrieve_by_id_nonexistent(
        self, retrieval: MemoryRetrievalService, scope: MemoryScope
    ) -> None:
        scoped_id = ScopedMemoryId(memory_id="nonexistent", scope=scope)
        assert await retrieval.retrieve_by_id(scoped_id) is None

    @pytest.mark.asyncio
    async def test_retrieve_by_type(
        self, retrieval: MemoryRetrievalService, populated_store: InMemoryStore, scope: MemoryScope
    ) -> None:
        results = await retrieval.retrieve_by_type("working", scope)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_retrieve_by_type_session(
        self, retrieval: MemoryRetrievalService, populated_store: InMemoryStore, scope: MemoryScope
    ) -> None:
        results = await retrieval.retrieve_by_type("session", scope)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_retrieve_by_tags(
        self, retrieval: MemoryRetrievalService, populated_store: InMemoryStore, scope: MemoryScope
    ) -> None:
        results = await retrieval.retrieve_by_tags(["a"], scope)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_retrieve_by_tags_no_match(
        self, retrieval: MemoryRetrievalService, populated_store: InMemoryStore, scope: MemoryScope
    ) -> None:
        results = await retrieval.retrieve_by_tags(["nonexistent"], scope)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_retrieve_related(
        self, retrieval: MemoryRetrievalService, populated_store: InMemoryStore, scope: MemoryScope
    ) -> None:
        scoped_id = ScopedMemoryId(memory_id="m1", scope=scope)
        results = await retrieval.retrieve_related(scoped_id, max_depth=1)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_retrieve_related_nonexistent(
        self, retrieval: MemoryRetrievalService, scope: MemoryScope
    ) -> None:
        scoped_id = ScopedMemoryId(memory_id="nonexistent", scope=scope)
        results = await retrieval.retrieve_related(scoped_id, max_depth=1)
        assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_related_with_relations(
        self, retrieval: MemoryRetrievalService, populated_store: InMemoryStore, scope: MemoryScope
    ) -> None:
        m1 = await retrieval.retrieve_by_id(ScopedMemoryId(memory_id="m1", scope=scope))
        assert m1 is not None
        updated = m1.model_copy(update={"related_ids": ("m2", "m3")})
        await populated_store.update(updated)

        scoped_id = ScopedMemoryId(memory_id="m1", scope=scope)
        results = await retrieval.retrieve_related(scoped_id, max_depth=1)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_retrieve_related_max_depth_zero(
        self, retrieval: MemoryRetrievalService, scope: MemoryScope
    ) -> None:
        scoped_id = ScopedMemoryId(memory_id="any", scope=scope)
        results = await retrieval.retrieve_related(scoped_id, max_depth=0)
        assert results == []

    @pytest.mark.asyncio
    async def test_search(
        self, retrieval: MemoryRetrievalService, populated_store: InMemoryStore, scope: MemoryScope
    ) -> None:
        query = MemoryQuery(query="first")
        result = await retrieval.search(query)
        assert result.total_count >= 1
        assert result.query == "first"
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_search_empty_query(
        self, retrieval: MemoryRetrievalService, populated_store: InMemoryStore, scope: MemoryScope
    ) -> None:
        query = MemoryQuery(query="")
        result = await retrieval.search(query)
        assert result.total_count == 3

    @pytest.mark.asyncio
    async def test_search_no_matches(
        self, retrieval: MemoryRetrievalService, populated_store: InMemoryStore, scope: MemoryScope
    ) -> None:
        query = MemoryQuery(query="zzzznonexistent")
        result = await retrieval.search(query)
        assert result.total_count == 0
