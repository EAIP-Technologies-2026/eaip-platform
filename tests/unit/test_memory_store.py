"""Tests for InMemoryStore and MemoryStoreAdapter."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.memory.exceptions import MemoryNotFoundError, MemoryValidationError
from eaip.memory.indexing import ContentIndexer
from eaip.memory.models import (
    MemoryItem,
    MemoryQuery,
    MemoryScope,
    MemoryStatus,
    MemoryType,
    ScopedMemoryId,
)
from eaip.memory.store import InMemoryStore, MemoryStoreAdapter


@pytest.fixture
def scope() -> MemoryScope:
    return MemoryScope(tenant_id="t1", user_id="u1")


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def sample_item(scope: MemoryScope) -> MemoryItem:
    return MemoryItem(
        memory_id="m1",
        memory_type=MemoryType.WORKING,
        scope=scope,
        content="test memory content",
        tags=("important", "test"),
        importance=0.8,
    )


class TestInMemoryStore:
    @pytest.mark.asyncio
    async def test_create_and_read(
        self, store: InMemoryStore, scope: MemoryScope, sample_item: MemoryItem
    ) -> None:
        created = await store.create(sample_item)
        assert created.memory_id == "m1"

        scoped_id = ScopedMemoryId(memory_id="m1", scope=scope)
        read = await store.read(scoped_id)
        assert read is not None
        assert read.content == "test memory content"

    @pytest.mark.asyncio
    async def test_create_duplicate_raises(
        self, store: InMemoryStore, scope: MemoryScope, sample_item: MemoryItem
    ) -> None:
        await store.create(sample_item)
        with pytest.raises(MemoryValidationError):
            await store.create(sample_item)

    @pytest.mark.asyncio
    async def test_read_nonexistent(self, store: InMemoryStore, scope: MemoryScope) -> None:
        scoped_id = ScopedMemoryId(memory_id="nonexistent", scope=scope)
        result = await store.read(scoped_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_update(
        self, store: InMemoryStore, scope: MemoryScope, sample_item: MemoryItem
    ) -> None:
        await store.create(sample_item)
        updated = sample_item.model_copy(update={"content": "updated content", "version": 2})
        result = await store.update(updated)
        assert result.version == 2
        assert result.content == "updated content"

    @pytest.mark.asyncio
    async def test_update_nonexistent_raises(
        self, store: InMemoryStore, scope: MemoryScope
    ) -> None:
        item = MemoryItem(
            memory_id="noexist", memory_type=MemoryType.WORKING, scope=scope, content="x"
        )
        with pytest.raises(MemoryNotFoundError):
            await store.update(item)

    @pytest.mark.asyncio
    async def test_delete(
        self, store: InMemoryStore, scope: MemoryScope, sample_item: MemoryItem
    ) -> None:
        await store.create(sample_item)
        scoped_id = ScopedMemoryId(memory_id="m1", scope=scope)
        assert await store.delete(scoped_id) is True
        assert await store.read(scoped_id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store: InMemoryStore, scope: MemoryScope) -> None:
        scoped_id = ScopedMemoryId(memory_id="noexist", scope=scope)
        assert await store.delete(scoped_id) is False

    @pytest.mark.asyncio
    async def test_archive_and_restore(
        self, store: InMemoryStore, scope: MemoryScope, sample_item: MemoryItem
    ) -> None:
        await store.create(sample_item)
        scoped_id = ScopedMemoryId(memory_id="m1", scope=scope)

        assert await store.archive(scoped_id) is True
        archived = await store.read(scoped_id)
        assert archived is not None
        assert archived.status is MemoryStatus.ARCHIVED

        assert await store.restore(scoped_id) is True
        restored = await store.read(scoped_id)
        assert restored is not None
        assert restored.status is MemoryStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_archive_nonexistent(self, store: InMemoryStore, scope: MemoryScope) -> None:
        scoped_id = ScopedMemoryId(memory_id="noexist", scope=scope)
        assert await store.archive(scoped_id) is False

    @pytest.mark.asyncio
    async def test_search(self, store: InMemoryStore, scope: MemoryScope) -> None:
        item1 = MemoryItem(
            memory_id="m1",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="hello world",
            tags=("greeting",),
        )
        item2 = MemoryItem(
            memory_id="m2",
            memory_type=MemoryType.SESSION,
            scope=scope,
            content="goodbye world",
            tags=("farewell",),
        )
        await store.create(item1)
        await store.create(item2)

        query = MemoryQuery(query="hello")
        results = await store.search(query)
        assert len(results) == 1
        assert results[0].memory.memory_id == "m1"

    @pytest.mark.asyncio
    async def test_search_with_type_filter(self, store: InMemoryStore, scope: MemoryScope) -> None:
        item1 = MemoryItem(
            memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="content"
        )
        item2 = MemoryItem(
            memory_id="m2", memory_type=MemoryType.SESSION, scope=scope, content="content"
        )
        await store.create(item1)
        await store.create(item2)

        query = MemoryQuery(query="content", memory_types=(MemoryType.WORKING,))
        results = await store.search(query)
        assert len(results) == 1
        assert results[0].memory.memory_type is MemoryType.WORKING

    @pytest.mark.asyncio
    async def test_search_with_tag_filter(self, store: InMemoryStore, scope: MemoryScope) -> None:
        item1 = MemoryItem(
            memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x", tags=("a",)
        )
        item2 = MemoryItem(
            memory_id="m2", memory_type=MemoryType.WORKING, scope=scope, content="x", tags=("b",)
        )
        await store.create(item1)
        await store.create(item2)

        query = MemoryQuery(query="x", tags=("a",))
        results = await store.search(query)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_list_by_scope(self, store: InMemoryStore, scope: MemoryScope) -> None:
        scope1 = MemoryScope(tenant_id="t1", user_id="u1")
        scope2 = MemoryScope(tenant_id="t2", user_id="u2")
        for i in range(3):
            await store.create(
                MemoryItem(
                    memory_id=f"m{i}", memory_type=MemoryType.WORKING, scope=scope1, content="x"
                )
            )
        await store.create(
            MemoryItem(
                memory_id="m_other", memory_type=MemoryType.WORKING, scope=scope2, content="x"
            )
        )

        items = await store.list_by_scope(scope1)
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_count_by_scope(self, store: InMemoryStore, scope: MemoryScope) -> None:
        for i in range(5):
            await store.create(
                MemoryItem(
                    memory_id=f"m{i}", memory_type=MemoryType.WORKING, scope=scope, content="x"
                )
            )
        count = await store.count_by_scope(scope)
        assert count == 5

    @pytest.mark.asyncio
    async def test_expire_before(self, store: InMemoryStore, scope: MemoryScope) -> None:
        past = datetime(2020, 1, 1, tzinfo=UTC)
        future = datetime(2030, 1, 1, tzinfo=UTC)
        item1 = MemoryItem(
            memory_id="m1",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="x",
            expires_at=past,
        )
        item2 = MemoryItem(
            memory_id="m2",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="x",
            expires_at=future,
        )
        await store.create(item1)
        await store.create(item2)

        expired = await store.expire_before(datetime(2025, 1, 1, tzinfo=UTC).timestamp())
        assert len(expired) == 1
        assert "m1" in expired[0]

    @pytest.mark.asyncio
    async def test_delete_many(self, store: InMemoryStore, scope: MemoryScope) -> None:
        for i in range(3):
            await store.create(
                MemoryItem(
                    memory_id=f"m{i}", memory_type=MemoryType.WORKING, scope=scope, content="x"
                )
            )
        smid = ScopedMemoryId(memory_id="m0", scope=scope)
        fq_ids = [smid.fully_qualified()]
        count = await store.delete_many(fq_ids)
        assert count == 1

    @pytest.mark.asyncio
    async def test_clear_scope(self, store: InMemoryStore, scope: MemoryScope) -> None:
        for i in range(3):
            await store.create(
                MemoryItem(
                    memory_id=f"m{i}", memory_type=MemoryType.WORKING, scope=scope, content="x"
                )
            )
        count = await store.clear_scope(scope)
        assert count == 3
        assert await store.count_by_scope(scope) == 0

    @pytest.mark.asyncio
    async def test_search_no_query_returns_all(
        self, store: InMemoryStore, scope: MemoryScope
    ) -> None:
        for i in range(3):
            await store.create(
                MemoryItem(
                    memory_id=f"m{i}", memory_type=MemoryType.WORKING, scope=scope, content="hello"
                )
            )
        query = MemoryQuery(query="")
        results = await store.search(query)
        assert len(results) == 3


class TestMemoryStoreAdapter:
    @pytest.mark.asyncio
    async def test_create_with_indexer(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        indexer = ContentIndexer()
        adapter = MemoryStoreAdapter(store, indexer=indexer)

        item = MemoryItem(
            memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="testable content"
        )
        created = await adapter.create(item)
        assert created.memory_id == "m1"

        query = MemoryQuery(query="testable")
        results = await adapter.search(query)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_update_with_reindex(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        indexer = ContentIndexer()
        adapter = MemoryStoreAdapter(store, indexer=indexer)

        item = MemoryItem(
            memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="original"
        )
        await adapter.create(item)

        updated = item.model_copy(update={"content": "updated"})
        await adapter.update(updated)

        query = MemoryQuery(query="updated")
        results = await adapter.search(query)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_delete_removes_from_index(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        indexer = ContentIndexer()
        adapter = MemoryStoreAdapter(store, indexer=indexer)

        item = MemoryItem(
            memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="delete me"
        )
        await adapter.create(item)

        scoped_id = ScopedMemoryId(memory_id="m1", scope=scope)
        assert await adapter.delete(scoped_id) is True

        query = MemoryQuery(query="delete")
        results = await adapter.search(query)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_archive_and_restore_via_adapter(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        adapter = MemoryStoreAdapter(store)

        item = MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x")
        await adapter.create(item)

        scoped_id = ScopedMemoryId(memory_id="m1", scope=scope)
        assert await adapter.archive(scoped_id) is True
        assert await adapter.restore(scoped_id) is True

    @pytest.mark.asyncio
    async def test_retrieve_by_id(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        adapter = MemoryStoreAdapter(store)

        item = MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x")
        await adapter.create(item)

        scoped_id = ScopedMemoryId(memory_id="m1", scope=scope)
        result = await adapter.retrieve_by_id(scoped_id)
        assert result is not None
        assert result.memory_id == "m1"

    @pytest.mark.asyncio
    async def test_retrieve_by_type(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        adapter = MemoryStoreAdapter(store)

        await adapter.create(
            MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x")
        )
        await adapter.create(
            MemoryItem(memory_id="m2", memory_type=MemoryType.SESSION, scope=scope, content="y")
        )

        results = await adapter.retrieve_by_type("working", scope)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_retrieve_by_tags(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        adapter = MemoryStoreAdapter(store)

        await adapter.create(
            MemoryItem(
                memory_id="m1",
                memory_type=MemoryType.WORKING,
                scope=scope,
                content="x",
                tags=("important",),
            )
        )
        results = await adapter.retrieve_by_tags(["important"], scope)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_delete_many(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        adapter = MemoryStoreAdapter(store)

        for i in range(3):
            await adapter.create(
                MemoryItem(
                    memory_id=f"m{i}", memory_type=MemoryType.WORKING, scope=scope, content="x"
                )
            )
        scoped_id = ScopedMemoryId(memory_id="m0", scope=scope)
        count = await adapter.delete_many([scoped_id.fully_qualified()])
        assert count == 1

    @pytest.mark.asyncio
    async def test_clear_scope(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        adapter = MemoryStoreAdapter(store)

        for i in range(3):
            await adapter.create(
                MemoryItem(
                    memory_id=f"m{i}", memory_type=MemoryType.WORKING, scope=scope, content="x"
                )
            )
        count = await adapter.clear_scope(scope)
        assert count == 3
