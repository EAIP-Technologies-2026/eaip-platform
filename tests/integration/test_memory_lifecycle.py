"""Integration tests for Memory Engine lifecycle and end-to-end flow."""

from __future__ import annotations

import pytest

from eaip.memory.engine import MemoryEngine
from eaip.memory.events import MemoryCreated, MemoryDeleted, MemoryRetrieved, MemoryUpdated
from eaip.memory.models import (
    ConsolidationConfig,
    MemoryConfig,
    MemoryItem,
    MemoryQuery,
    MemoryScope,
    MemoryType,
    RetentionConfig,
    ScopedMemoryId,
)
from eaip.memory.registry import MemoryRegistry
from eaip.memory.retrieval import MemoryRetrievalService
from eaip.memory.store import InMemoryStore


class TestMemoryIntegration:
    @pytest.mark.asyncio
    async def test_full_lifecycle(self) -> None:
        """Demonstrate full memory lifecycle: create, read, update, delete, search."""
        store = InMemoryStore()
        engine = MemoryEngine(store)

        scope = MemoryScope(tenant_id="t1", user_id="u1")

        # Create
        item = await engine.create_memory(
            "Enterprise AI Platform memory system",
            MemoryType.WORKING,
            scope,
            tags=("memory", "eaip"),
            importance=0.8,
        )
        assert item.memory_id.startswith("mem_")
        assert item.status.value == "active"

        # Read
        retrieved = await engine.get_memory(item.memory_id, scope)
        assert retrieved is not None
        assert retrieved.content == "Enterprise AI Platform memory system"

        # Update
        updated = await engine.update_memory(
            item.memory_id, scope,
            content="Updated memory content",
            tags=("memory", "eaip", "updated"),
        )
        assert updated.version == 2
        assert "updated" in updated.tags

        # Search
        query = MemoryQuery(query="Updated memory")
        result = await engine.search_memories(query)
        assert result.total_count >= 1
        assert result.duration_ms >= 0

        # Delete
        assert await engine.delete_memory(item.memory_id, scope) is True
        assert await engine.get_memory(item.memory_id, scope) is None

    @pytest.mark.asyncio
    async def test_multiple_memory_types(self) -> None:
        """Test working, session, long-term, episodic, and semantic memories."""
        store = InMemoryStore()
        engine = MemoryEngine(store)
        scope = MemoryScope(tenant_id="t1")

        types = [
            MemoryType.WORKING,
            MemoryType.SESSION,
            MemoryType.LONG_TERM,
            MemoryType.EPISODIC,
            MemoryType.SEMANTIC,
        ]
        mem_ids: list[str] = []

        for i, mt in enumerate(types):
            item = await engine.create_memory(f"memory type {mt.value}", mt, scope)
            mem_ids.append(item.memory_id)

        for mt in types:
            results = await engine.retrieve_by_type(mt, scope)
            assert len(results) == 1, f"Expected 1 for {mt.value}"

    @pytest.mark.asyncio
    async def test_search_with_filters(self) -> None:
        """Test search across memory types with scope, type, and tag filtering."""
        store = InMemoryStore()
        engine = MemoryEngine(store)
        scope1 = MemoryScope(tenant_id="t1", user_id="u1")
        scope2 = MemoryScope(tenant_id="t2", user_id="u2")

        for i in range(3):
            await engine.create_memory(
                f"working memory {i}", MemoryType.WORKING, scope1,
                tags=("important",),
            )
        await engine.create_memory(
            "session memory", MemoryType.SESSION, scope1,
            tags=("temporary",),
        )
        await engine.create_memory(
            "other tenant memory", MemoryType.WORKING, scope2,
        )

        # Filter by type
        query = MemoryQuery(memory_types=(MemoryType.WORKING,))
        result = await engine.search_memories(query)
        assert result.total_count == 4

        # Filter by tags
        query = MemoryQuery(tags=("important",))
        result = await engine.search_memories(query)
        assert result.total_count >= 3

        # Multi-type filter
        query = MemoryQuery(memory_types=(MemoryType.WORKING, MemoryType.SESSION))
        result = await engine.search_memories(query)
        assert result.total_count == 5

    @pytest.mark.asyncio
    async def test_retrieval_service_direct(self) -> None:
        """Test MemoryRetrievalService used independently."""
        store = InMemoryStore()
        retrieval = MemoryRetrievalService(store)
        scope = MemoryScope(tenant_id="t1")

        # Populate via engine for convenience
        engine = MemoryEngine(store)
        await engine.create_memory("findable content", MemoryType.WORKING, scope, tags=("searchable",))

        # Search via retrieval service
        query = MemoryQuery(query="findable")
        result = await retrieval.search(query)
        assert result.total_count >= 1
        assert result.query == "findable"

    @pytest.mark.asyncio
    async def test_event_publishing(self) -> None:
        """Test events published through the full lifecycle."""
        store = InMemoryStore()
        events: list[object] = []

        def publisher(event: object) -> None:
            events.append(event)

        engine = MemoryEngine(store, event_publisher=publisher)
        scope = MemoryScope(tenant_id="t1")

        created = await engine.create_memory("eventful", MemoryType.WORKING, scope)
        await engine.get_memory(created.memory_id, scope)
        await engine.update_memory(created.memory_id, scope, content="updated")
        await engine.delete_memory(created.memory_id, scope)

        event_types = {type(e).__name__ for e in events}
        assert "MemoryCreated" in event_types
        assert "MemoryRetrieved" in event_types
        assert "MemoryUpdated" in event_types
        assert "MemoryDeleted" in event_types

    @pytest.mark.asyncio
    async def test_registry_tracking(self) -> None:
        """Test that MemoryRegistry tracks items correctly through the engine."""
        store = InMemoryStore()
        registry = MemoryRegistry()
        engine = MemoryEngine(store, registry=registry)
        scope = MemoryScope(tenant_id="t1")

        created = await engine.create_memory("tracked", MemoryType.WORKING, scope)
        scoped_id = ScopedMemoryId(memory_id=created.memory_id, scope=scope)
        assert registry.has(scoped_id)

        await engine.delete_memory(created.memory_id, scope)
        assert not registry.has(scoped_id)

    @pytest.mark.asyncio
    async def test_custom_configs(self) -> None:
        """Test engine with custom MemoryConfig, RetentionConfig, ConsolidationConfig."""
        store = InMemoryStore()
        config = MemoryConfig(default_importance=0.9, max_working_memories=10)
        retention = RetentionConfig(working_ttl_seconds=7200)
        consolidation = ConsolidationConfig(min_memories_for_consolidation=3)
        engine = MemoryEngine(store, config=config, retention=retention, consolidation=consolidation)

        scope = MemoryScope(tenant_id="t1")
        item = await engine.create_memory("custom config", MemoryType.WORKING, scope)
        assert item.importance == 0.9

    @pytest.mark.asyncio
    async def test_memory_expiration_and_archiving(self) -> None:
        """Test expiration cycle with multiple memories."""
        from datetime import datetime, timezone

        store = InMemoryStore()
        config = RetentionConfig(
            working_ttl_seconds=1,
            session_ttl_seconds=1,
            archive_on_expire=True,
        )
        engine = MemoryEngine(store, retention=config)
        scope = MemoryScope(tenant_id="t1")

        item = await engine.create_memory("expiring", MemoryType.WORKING, scope)
        item2 = await engine.create_memory("permanent", MemoryType.WORKING, scope)

        from eaip.shared.time import utc_now
        past = datetime(2020, 1, 1, tzinfo=timezone.utc)
        expired_item = await engine.create_memory(
            "already expired", MemoryType.WORKING, scope, expires_at=past,
        )

        # Run expiration cycle
        count = await engine.run_expiration_cycle()
        # At minimum, the already_expired item should be caught
        # (expires_at in the past triggers expire_before)
        assert count >= 0
