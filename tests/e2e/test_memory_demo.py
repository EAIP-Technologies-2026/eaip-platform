"""End-to-end test demonstrating the complete Memory Engine workflow.

Demonstrates:
- Creating memories of all five types (working, session, long-term, episodic, semantic)
- Retrieval by ID, type, and tags
- Search with content, type, and tag filters
- Memory updates with version tracking
- Memory archiving and expiration
- Memory consolidation
- Event publishing
- Health reporting
"""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.memory.engine import MemoryEngine
from eaip.memory.health import MemoryHealthCheck
from eaip.memory.models import (
    MemoryConfig,
    MemoryQuery,
    MemoryScope,
    MemoryType,
    RetentionConfig,
)
from eaip.memory.registry import MemoryRegistry
from eaip.memory.store import InMemoryStore


class TestMemoryE2E:
    @pytest.mark.asyncio
    async def test_e2e_memory_workflow(self) -> None:
        """Demonstrate a complete Memory Engine workflow."""
        store = InMemoryStore()
        registry = MemoryRegistry()
        events: list[str] = []

        def publisher(event: object) -> None:
            events.append(type(event).__name__)

        engine = MemoryEngine(
            store,
            registry=registry,
            event_publisher=publisher,
            config=MemoryConfig(default_importance=0.5),
            retention=RetentionConfig(working_ttl_seconds=3600),
        )

        scope = MemoryScope(tenant_id="t1", user_id="u1", session_id="s1")

        # 1. Create memories of all five types
        working = await engine.create_memory(
            "Current task context for code review",
            MemoryType.WORKING,
            scope,
            tags=("active", "code-review"),
            importance=0.9,
        )
        assert working.memory_type is MemoryType.WORKING

        session = await engine.create_memory(
            "User asked about memory engine architecture",
            MemoryType.SESSION,
            scope,
            tags=("conversation", "architecture"),
        )
        assert session.memory_type is MemoryType.SESSION

        long_term = await engine.create_memory(
            "The EAIP platform uses a multi-tier memory architecture",
            MemoryType.LONG_TERM,
            scope,
            tags=("architecture", "persistent"),
            importance=0.8,
        )
        assert long_term.memory_type is MemoryType.LONG_TERM

        episodic = await engine.create_memory(
            "User reported a bug in the retrieval service at 2026-07-09",
            MemoryType.EPISODIC,
            scope,
            tags=("bug", "incident"),
        )
        assert episodic.memory_type is MemoryType.EPISODIC

        semantic = await engine.create_memory(
            "Memory retrieval performance degrades with more than 10K items",
            MemoryType.SEMANTIC,
            scope,
            tags=("performance", "knowledge"),
            importance=0.95,
        )
        assert semantic.memory_type is MemoryType.SEMANTIC

        # 2. Retrieve by ID
        retrieved = await engine.get_memory(working.memory_id, scope)
        assert retrieved is not None
        assert retrieved.content == working.content

        # 3. Retrieve by type
        working_results = await engine.retrieve_by_type(MemoryType.WORKING, scope)
        assert len(working_results) == 1

        episodic_results = await engine.retrieve_by_type(MemoryType.EPISODIC, scope)
        assert len(episodic_results) == 1

        # 4. Retrieve by tags
        arch_results = await engine.retrieve_by_tags(["architecture"], scope)
        assert len(arch_results) >= 1

        # 5. Search with content query
        query = MemoryQuery(query="memory architecture")
        results = await engine.search_memories(query)
        assert results.total_count >= 1
        assert results.duration_ms >= 0
        assert results.query == "memory architecture"

        # 6. Search with type filter
        query = MemoryQuery(
            query="memory",
            memory_types=(MemoryType.WORKING, MemoryType.SESSION),
        )
        results = await engine.search_memories(query)
        assert results.total_count >= 1

        # 7. Search with tag filter
        query = MemoryQuery(tags=("performance",))
        results = await engine.search_memories(query)
        assert results.total_count >= 1

        # 8. Update memory with version tracking
        updated = await engine.update_memory(
            long_term.memory_id,
            scope,
            content="Updated: EAIP uses a multi-tier memory architecture with vector search",
            tags=("architecture", "persistent", "updated"),
        )
        assert updated.version == 2
        assert "updated" in updated.tags

        # 9. Archive a memory
        assert await engine.archive_memory(session.memory_id, scope) is True

        # 10. Verify archived memory is retrievable
        archived = await engine.get_memory(session.memory_id, scope)
        assert archived is not None
        assert archived.status.value == "archived"

        # 11. Run expiration cycle
        expired_count = await engine.run_expiration_cycle()
        assert expired_count >= 0

        # 12. Run consolidation
        report = await engine.consolidate(MemoryType.EPISODIC, scope)
        assert report is not None

        # 13. Health check
        health_check = MemoryHealthCheck(engine)
        report = await health_check.check()
        assert report.component == "memory"
        assert report.status is HealthStatus.HEALTHY

        # 14. Clear scope
        count = await engine.clear_scope(scope)
        assert count > 0

        # 15. Verify scope cleared
        remaining = await engine.retrieve_by_type(MemoryType.WORKING, scope)
        assert len(remaining) == 0

        # 16. Verify events were published
        event_names = set(events)
        assert "MemoryCreated" in event_names
        assert "MemoryUpdated" in event_names
        assert "MemoryArchived" in event_names
