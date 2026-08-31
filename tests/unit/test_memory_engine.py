"""Tests for the MemoryEngine orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.memory.engine import MemoryEngine
from eaip.memory.events import (
    MemoryArchived,
    MemoryCreated,
    MemoryDeleted,
    MemoryExpired,
    MemoryRetrieved,
    MemorySearchExecuted,
    MemoryUpdated,
)
from eaip.memory.exceptions import MemoryNotFoundError
from eaip.memory.models import (
    MemoryConfig,
    MemoryQuery,
    MemoryScope,
    MemoryStatus,
    MemoryType,
    RetentionConfig,
    ScopedMemoryId,
)
from eaip.memory.store import InMemoryStore


@pytest.fixture
def scope() -> MemoryScope:
    return MemoryScope(tenant_id="t1", user_id="u1")


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def engine(store: InMemoryStore) -> MemoryEngine:
    return MemoryEngine(store)


class TestMemoryEngine:
    @pytest.mark.asyncio
    async def test_create_memory(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        item = await engine.create_memory("hello world", MemoryType.WORKING, scope)
        assert item.memory_id.startswith("mem_")
        assert item.content == "hello world"
        assert item.memory_type is MemoryType.WORKING
        assert item.status is MemoryStatus.ACTIVE
        assert item.version == 1

    @pytest.mark.asyncio
    async def test_create_memory_with_tags_and_metadata(
        self, engine: MemoryEngine, scope: MemoryScope
    ) -> None:
        item = await engine.create_memory(
            "tagged memory",
            MemoryType.EPISODIC,
            scope,
            tags=("important", "test"),
            metadata={"source": "test"},
            importance=0.9,
        )
        assert "important" in item.tags
        assert item.metadata["source"] == "test"
        assert item.importance == 0.9

    @pytest.mark.asyncio
    async def test_create_memory_with_importance_clamped(
        self, engine: MemoryEngine, scope: MemoryScope
    ) -> None:
        item = await engine.create_memory("x", MemoryType.WORKING, scope, importance=2.0)
        assert item.importance == 1.0

    @pytest.mark.asyncio
    async def test_create_memory_with_expires_at(
        self, engine: MemoryEngine, scope: MemoryScope
    ) -> None:
        dt = datetime(2026, 12, 31, tzinfo=UTC)
        item = await engine.create_memory("x", MemoryType.WORKING, scope, expires_at=dt)
        assert item.expires_at == dt

    @pytest.mark.asyncio
    async def test_create_memory_with_embedding(
        self, engine: MemoryEngine, scope: MemoryScope
    ) -> None:
        emb = (0.1, 0.2, 0.3)
        item = await engine.create_memory("x", MemoryType.WORKING, scope, embedding=emb)
        assert item.embedding == emb

    @pytest.mark.asyncio
    async def test_get_memory(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        await engine.create_memory("found me", MemoryType.WORKING, scope)
        item = await engine.get_memory("mem_unknown", scope)
        assert item is None

    @pytest.mark.asyncio
    async def test_get_memory_increments_access_count(
        self, engine: MemoryEngine, scope: MemoryScope
    ) -> None:
        created = await engine.create_memory("test", MemoryType.WORKING, scope)
        await engine.get_memory(created.memory_id, scope)
        stored = await engine.store.read(ScopedMemoryId(memory_id=created.memory_id, scope=scope))
        assert stored is not None
        assert stored.access_count >= 1

    @pytest.mark.asyncio
    async def test_update_memory(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        created = await engine.create_memory("original", MemoryType.WORKING, scope)
        updated = await engine.update_memory(created.memory_id, scope, content="updated content")
        assert updated.content == "updated content"
        assert updated.version == 2

    @pytest.mark.asyncio
    async def test_update_memory_tags(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        created = await engine.create_memory("x", MemoryType.WORKING, scope, tags=("old",))
        updated = await engine.update_memory(created.memory_id, scope, tags=("new",))
        assert updated.tags == ("new",)

    @pytest.mark.asyncio
    async def test_update_memory_metadata_merged(
        self, engine: MemoryEngine, scope: MemoryScope
    ) -> None:
        created = await engine.create_memory("x", MemoryType.WORKING, scope, metadata={"a": 1})
        updated = await engine.update_memory(created.memory_id, scope, metadata={"b": 2})
        assert updated.metadata == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_update_nonexistent_memory_raises(
        self, engine: MemoryEngine, scope: MemoryScope
    ) -> None:
        with pytest.raises(MemoryNotFoundError):
            await engine.update_memory("nonexistent", scope, content="x")

    @pytest.mark.asyncio
    async def test_delete_memory(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        created = await engine.create_memory("delete me", MemoryType.WORKING, scope)
        assert await engine.delete_memory(created.memory_id, scope) is True
        assert await engine.get_memory(created.memory_id, scope) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(
        self, engine: MemoryEngine, scope: MemoryScope
    ) -> None:
        assert await engine.delete_memory("nonexistent", scope) is False

    @pytest.mark.asyncio
    async def test_search_memories(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        await engine.create_memory("search target", MemoryType.WORKING, scope)
        await engine.create_memory("other content", MemoryType.SESSION, scope)

        query = MemoryQuery(query="search")
        result = await engine.search_memories(query)
        assert result.total_count >= 1

    @pytest.mark.asyncio
    async def test_search_memories_empty(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        query = MemoryQuery(query="nonexistent")
        result = await engine.search_memories(query)
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_retrieve_by_type(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        await engine.create_memory("working", MemoryType.WORKING, scope)
        await engine.create_memory("session", MemoryType.SESSION, scope)

        results = await engine.retrieve_by_type(MemoryType.WORKING, scope)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_retrieve_by_tags(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        await engine.create_memory("tagged", MemoryType.WORKING, scope, tags=("important",))
        results = await engine.retrieve_by_tags(["important"], scope)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_clear_scope(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        await engine.create_memory("a", MemoryType.WORKING, scope)
        await engine.create_memory("b", MemoryType.WORKING, scope)
        count = await engine.clear_scope(scope)
        assert count == 2

    @pytest.mark.asyncio
    async def test_consolidate(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        for i in range(5):
            await engine.create_memory(f"event {i}", MemoryType.EPISODIC, scope)
        report = await engine.consolidate(MemoryType.EPISODIC, scope)
        assert report is not None

    @pytest.mark.asyncio
    async def test_expire_memory(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        created = await engine.create_memory("expire me", MemoryType.WORKING, scope)
        assert await engine.expire_memory(created.memory_id, scope) is True

    @pytest.mark.asyncio
    async def test_archive_memory(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        created = await engine.create_memory("archive me", MemoryType.WORKING, scope)
        assert await engine.archive_memory(created.memory_id, scope) is True

    @pytest.mark.asyncio
    async def test_run_expiration_cycle(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        count = await engine.run_expiration_cycle()
        assert count >= 0

    @pytest.mark.asyncio
    async def test_summarize_without_summarizer(
        self, engine: MemoryEngine, scope: MemoryScope
    ) -> None:
        created = await engine.create_memory("summary test", MemoryType.WORKING, scope)
        result = await engine.summarize([created.memory_id], scope)
        assert result is None

    @pytest.mark.asyncio
    async def test_health(self, engine: MemoryEngine, scope: MemoryScope) -> None:
        await engine.create_memory("health check", MemoryType.WORKING, scope)
        health = await engine.health()
        assert health["status"] == "healthy"
        assert health["items"] >= 1

    @pytest.mark.asyncio
    async def test_properties(self, engine: MemoryEngine) -> None:
        assert engine.store is not None
        assert engine.registry is not None
        assert engine.retrieval is not None
        assert engine.lifecycle is not None

    def test_store_property(self, engine: MemoryEngine) -> None:
        assert isinstance(engine.store, InMemoryStore)

    def test_on_event_handler(self, engine: MemoryEngine) -> None:
        engine.on(MemoryCreated, lambda e: None)

    @pytest.mark.asyncio
    async def test_engine_with_custom_config(self) -> None:
        store = InMemoryStore()
        config = MemoryConfig(default_importance=0.7, enable_expiration=False)
        engine = MemoryEngine(store, config=config)
        assert engine._config.default_importance == 0.7

    @pytest.mark.asyncio
    async def test_engine_with_custom_retention(self) -> None:
        store = InMemoryStore()
        retention = RetentionConfig(working_ttl_seconds=500)
        engine = MemoryEngine(store, retention=retention)
        assert engine._expiration._config.working_ttl_seconds == 500


class TestMemoryEngineAuthorization:
    @pytest.mark.asyncio
    async def test_authorize_called_on_create(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        called: list[str] = []

        def authorize(action: str, _scope: MemoryScope) -> None:
            called.append(action)

        engine = MemoryEngine(store, authorize_fn=authorize)
        await engine.create_memory("x", MemoryType.WORKING, scope)
        assert "create_memory" in called

    @pytest.mark.asyncio
    async def test_authorize_called_on_get(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        called: list[str] = []

        def authorize(action: str, _scope: MemoryScope) -> None:
            called.append(action)

        engine = MemoryEngine(store, authorize_fn=authorize)
        await engine.get_memory("nonexistent", scope)
        assert "get_memory" in called

    @pytest.mark.asyncio
    async def test_authorize_called_on_update(
        self, engine: MemoryEngine, scope: MemoryScope
    ) -> None:
        store = InMemoryStore()
        called: list[str] = []

        def authorize(action: str, _scope: MemoryScope) -> None:
            called.append(action)

        engine = MemoryEngine(store, authorize_fn=authorize)
        with pytest.raises(MemoryNotFoundError):
            await engine.update_memory("nonexistent", scope, content="x")
        assert "update_memory" in called


class TestMemoryEngineEvents:
    @pytest.mark.asyncio
    async def test_create_publishes_event(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        events: list[object] = []

        def publisher(event: object) -> None:
            events.append(event)

        engine = MemoryEngine(store, event_publisher=publisher)
        await engine.create_memory("event test", MemoryType.WORKING, scope)
        assert any(isinstance(e, MemoryCreated) for e in events)

    @pytest.mark.asyncio
    async def test_update_publishes_event(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        events: list[object] = []

        def publisher(event: object) -> None:
            events.append(event)

        engine = MemoryEngine(store, event_publisher=publisher)
        created = await engine.create_memory("x", MemoryType.WORKING, scope)
        await engine.update_memory(created.memory_id, scope, content="y")
        assert any(isinstance(e, MemoryUpdated) for e in events)

    @pytest.mark.asyncio
    async def test_delete_publishes_event(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        events: list[object] = []

        def publisher(event: object) -> None:
            events.append(event)

        engine = MemoryEngine(store, event_publisher=publisher)
        created = await engine.create_memory("x", MemoryType.WORKING, scope)
        await engine.delete_memory(created.memory_id, scope)
        assert any(isinstance(e, MemoryDeleted) for e in events)

    @pytest.mark.asyncio
    async def test_get_publishes_retrieved(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        events: list[object] = []

        def publisher(event: object) -> None:
            events.append(event)

        engine = MemoryEngine(store, event_publisher=publisher)
        created = await engine.create_memory("x", MemoryType.WORKING, scope)
        await engine.get_memory(created.memory_id, scope)
        assert any(isinstance(e, MemoryRetrieved) for e in events)

    @pytest.mark.asyncio
    async def test_search_publishes_event(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        events: list[object] = []

        def publisher(event: object) -> None:
            events.append(event)

        engine = MemoryEngine(store, event_publisher=publisher)
        await engine.create_memory("x", MemoryType.WORKING, scope)
        query = MemoryQuery(query="x")
        await engine.search_memories(query)
        assert any(isinstance(e, MemorySearchExecuted) for e in events)

    @pytest.mark.asyncio
    async def test_expire_publishes_event(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        events: list[object] = []

        def publisher(event: object) -> None:
            events.append(event)

        engine = MemoryEngine(store, event_publisher=publisher)
        created = await engine.create_memory("x", MemoryType.WORKING, scope)
        await engine.expire_memory(created.memory_id, scope)
        assert any(isinstance(e, MemoryExpired) for e in events)

    @pytest.mark.asyncio
    async def test_archive_publishes_event(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        events: list[object] = []

        def publisher(event: object) -> None:
            events.append(event)

        engine = MemoryEngine(store, event_publisher=publisher)
        created = await engine.create_memory("x", MemoryType.WORKING, scope)
        await engine.archive_memory(created.memory_id, scope)
        assert any(isinstance(e, MemoryArchived) for e in events)

    @pytest.mark.asyncio
    async def test_event_publisher_failure_does_not_raise(self, scope: MemoryScope) -> None:
        store = InMemoryStore()

        def failing_publisher(_event: object) -> None:
            raise RuntimeError("publisher failed")

        engine = MemoryEngine(store, event_publisher=failing_publisher)
        item = await engine.create_memory("x", MemoryType.WORKING, scope)
        assert item is not None


class TestMemoryEngineHooks:
    @pytest.mark.asyncio
    async def test_before_and_after_store_hooks(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        calls: list[str] = []

        def hook(scope_arg: MemoryScope) -> None:
            calls.append(scope_arg.scope_key())

        hooks = {
            "before_store": [hook],
            "after_store": [hook],
        }

        engine = MemoryEngine(store, hooks=hooks)
        await engine.create_memory("x", MemoryType.WORKING, scope)
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_before_and_after_delete_hooks(self, scope: MemoryScope) -> None:
        store = InMemoryStore()
        calls: list[str] = []

        def hook(_scope: MemoryScope) -> None:
            calls.append("called")

        hooks = {
            "before_delete": [hook],
            "after_delete": [hook],
        }

        engine = MemoryEngine(store, hooks=hooks)
        created = await engine.create_memory("x", MemoryType.WORKING, scope)
        await engine.delete_memory(created.memory_id, scope)
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_hook_failure_does_not_raise(self, scope: MemoryScope) -> None:
        store = InMemoryStore()

        def failing_hook(_scope: MemoryScope) -> None:
            raise RuntimeError("hook failed")

        hooks = {"before_store": [failing_hook]}

        engine = MemoryEngine(store, hooks=hooks)
        item = await engine.create_memory("x", MemoryType.WORKING, scope)
        assert item is not None
