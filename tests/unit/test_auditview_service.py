"""Tests for AuditViewer."""

from __future__ import annotations

import pytest

from eaip.auditview.exceptions import EntryNotFoundError
from eaip.auditview.models import AuditFilter, AuditLogEntry, ViewerConfig
from eaip.auditview.viewer import AuditViewer


class TestAuditViewer:
    @pytest.fixture
    def viewer(self) -> AuditViewer:
        return AuditViewer()

    @pytest.fixture
    def sample_entry(self) -> AuditLogEntry:
        return AuditLogEntry(
            id="e1",
            actor="user1",
            action="create",
            resource="resource:123",
            correlation_id="corr1",
        )

    class TestIngestEntry:
        async def test_ingest(self, viewer: AuditViewer, sample_entry: AuditLogEntry) -> None:
            result = await viewer.ingest_entry(sample_entry)
            assert result.id == "e1"
            assert result.actor == "user1"

        async def test_ingest_multiple(
            self, viewer: AuditViewer, sample_entry: AuditLogEntry
        ) -> None:
            await viewer.ingest_entry(sample_entry)
            e2 = AuditLogEntry(id="e2", actor="user2", action="delete", resource="res:456")
            await viewer.ingest_entry(e2)
            stats = await viewer.get_statistics()
            assert stats["total_entries"] == 2

    class TestSearchEntries:
        async def test_search_all(self, viewer: AuditViewer, sample_entry: AuditLogEntry) -> None:
            await viewer.ingest_entry(sample_entry)
            result = await viewer.search_entries()
            assert result.total == 1

        async def test_search_filter_actor(
            self, viewer: AuditViewer, sample_entry: AuditLogEntry
        ) -> None:
            await viewer.ingest_entry(sample_entry)
            filter_ = AuditFilter(actor="user1")
            result = await viewer.search_entries(filter_)
            assert result.total == 1

            filter_ = AuditFilter(actor="nonexistent")
            result = await viewer.search_entries(filter_)
            assert result.total == 0

        async def test_search_filter_action(
            self, viewer: AuditViewer, sample_entry: AuditLogEntry
        ) -> None:
            await viewer.ingest_entry(sample_entry)
            filter_ = AuditFilter(action="create")
            result = await viewer.search_entries(filter_)
            assert result.total == 1

        async def test_search_pagination(
            self, viewer: AuditViewer, sample_entry: AuditLogEntry
        ) -> None:
            await viewer.ingest_entry(sample_entry)
            filter_ = AuditFilter(limit=1, offset=0)
            result = await viewer.search_entries(filter_)
            assert len(result.entries) == 1
            assert result.has_more is False

    class TestGetEntry:
        async def test_get(self, viewer: AuditViewer, sample_entry: AuditLogEntry) -> None:
            await viewer.ingest_entry(sample_entry)
            entry = await viewer.get_entry("e1")
            assert entry.actor == "user1"

        async def test_not_found(self, viewer: AuditViewer) -> None:
            with pytest.raises(EntryNotFoundError):
                await viewer.get_entry("nonexistent")

    class TestGetActorHistory:
        async def test_history(self, viewer: AuditViewer, sample_entry: AuditLogEntry) -> None:
            await viewer.ingest_entry(sample_entry)
            history = await viewer.get_actor_history("user1")
            assert len(history) == 1

        async def test_history_empty(self, viewer: AuditViewer) -> None:
            history = await viewer.get_actor_history("nonexistent")
            assert len(history) == 0

    class TestGetResourceTimeline:
        async def test_timeline(self, viewer: AuditViewer, sample_entry: AuditLogEntry) -> None:
            await viewer.ingest_entry(sample_entry)
            timeline = await viewer.get_resource_timeline("resource:123")
            assert len(timeline) == 1

    class TestExportEntries:
        async def test_export(self, viewer: AuditViewer, sample_entry: AuditLogEntry) -> None:
            await viewer.ingest_entry(sample_entry)
            exported = await viewer.export_entries()
            assert len(exported) == 1
            assert exported[0]["actor"] == "user1"

    class TestGetStatistics:
        async def test_statistics(self, viewer: AuditViewer, sample_entry: AuditLogEntry) -> None:
            await viewer.ingest_entry(sample_entry)
            stats = await viewer.get_statistics()
            assert stats["total_entries"] == 1
            assert stats["unique_actors"] == 1
            assert stats["unique_actions"] == 1

        async def test_statistics_empty(self, viewer: AuditViewer) -> None:
            stats = await viewer.get_statistics()
            assert stats["total_entries"] == 0

    class TestConfig:
        def test_default_config(self) -> None:
            v = AuditViewer()
            assert v.config.max_export_limit == 10000
            assert v.config.default_page_size == 50

        def test_custom_config(self) -> None:
            config = ViewerConfig(max_export_limit=5000, default_page_size=25)
            v = AuditViewer(config=config)
            assert v.config.max_export_limit == 5000
            assert v.config.default_page_size == 25
