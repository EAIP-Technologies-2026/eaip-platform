"""Tests for Archive domain models."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.archive.models import (
    ArchiveConfig,
    ArchiveManifest,
    ArchiveQuery,
    ArchiveRecord,
    ArchiveResult,
    CleanupReport,
    RetentionPolicy,
)


class TestArchiveConfig:
    def test_defaults(self) -> None:
        c = ArchiveConfig()
        assert c.storage_backend == "local"
        assert c.compression_enabled is True
        assert c.retention_days == 365
        assert c.schedule_cron is None

    def test_custom(self) -> None:
        c = ArchiveConfig(
            storage_backend="s3",
            compression_enabled=False,
            retention_days=90,
            schedule_cron="0 2 * * *",
        )
        assert c.storage_backend == "s3"
        assert c.compression_enabled is False
        assert c.retention_days == 90
        assert c.schedule_cron == "0 2 * * *"

    def test_frozen(self) -> None:
        c = ArchiveConfig()
        with pytest.raises(ValueError):
            c.storage_backend = "s3"  # type: ignore[misc]


class TestArchiveRecord:
    def test_required_fields(self) -> None:
        r = ArchiveRecord(record_id="rec_1", source_collection="orders")
        assert r.record_id == "rec_1"
        assert r.source_collection == "orders"
        assert isinstance(r.archived_at, datetime)
        assert r.size_bytes == 0
        assert r.checksum == ""
        assert r.location == ""
        assert r.metadata == {}

    def test_with_all_fields(self) -> None:
        now = datetime.now()
        r = ArchiveRecord(
            record_id="rec_1",
            source_collection="orders",
            archived_at=now,
            size_bytes=1024,
            checksum="abc123",
            location="/archive/orders/rec_1",
            metadata={"env": "prod"},
        )
        assert r.size_bytes == 1024
        assert r.checksum == "abc123"
        assert r.location == "/archive/orders/rec_1"
        assert r.metadata == {"env": "prod"}

    def test_frozen(self) -> None:
        r = ArchiveRecord(record_id="r1", source_collection="c1")
        with pytest.raises(ValueError):
            r.source_collection = "c2"  # type: ignore[misc]


class TestArchiveManifest:
    def test_required_fields(self) -> None:
        m = ArchiveManifest(manifest_id="m_1")
        assert m.manifest_id == "m_1"
        assert m.records == ()
        assert m.total_size == 0
        assert isinstance(m.created_at, datetime)
        assert m.status == "created"

    def test_with_records(self) -> None:
        r1 = ArchiveRecord(record_id="r1", source_collection="c1")
        r2 = ArchiveRecord(record_id="r2", source_collection="c2")
        m = ArchiveManifest(
            manifest_id="m_1",
            records=(r1, r2),
            total_size=2048,
            status="completed",
        )
        assert len(m.records) == 2
        assert m.total_size == 2048
        assert m.status == "completed"

    def test_frozen(self) -> None:
        m = ArchiveManifest(manifest_id="m1")
        with pytest.raises(ValueError):
            m.status = "failed"  # type: ignore[misc]


class TestRetentionPolicy:
    def test_required_fields(self) -> None:
        p = RetentionPolicy(policy_id="p_1", name="Delete old orders")
        assert p.policy_id == "p_1"
        assert p.name == "Delete old orders"
        assert p.max_age_days == 0
        assert p.max_size_bytes == 0
        assert p.action == "delete"
        assert p.priority == 0

    def test_custom(self) -> None:
        p = RetentionPolicy(
            policy_id="p_1",
            name="Compress large records",
            max_age_days=90,
            max_size_bytes=1073741824,
            action="compress",
            priority=10,
        )
        assert p.max_age_days == 90
        assert p.max_size_bytes == 1073741824
        assert p.action == "compress"
        assert p.priority == 10

    def test_frozen(self) -> None:
        p = RetentionPolicy(policy_id="p1", name="N")
        with pytest.raises(ValueError):
            p.name = "changed"  # type: ignore[misc]


class TestArchiveQuery:
    def test_defaults(self) -> None:
        q = ArchiveQuery()
        assert q.filters == {}
        assert q.date_from is None
        assert q.date_to is None
        assert q.limit == 100
        assert q.offset == 0

    def test_with_filters(self) -> None:
        q = ArchiveQuery(
            filters={"source_collection": "orders"},
            limit=50,
            offset=10,
        )
        assert q.filters == {"source_collection": "orders"}
        assert q.limit == 50
        assert q.offset == 10

    def test_frozen(self) -> None:
        q = ArchiveQuery()
        with pytest.raises(ValueError):
            q.limit = 200  # type: ignore[misc]


class TestArchiveResult:
    def test_defaults(self) -> None:
        r = ArchiveResult()
        assert r.records == ()
        assert r.total_count == 0
        assert r.page == 1
        assert r.page_size == 100

    def test_with_data(self) -> None:
        rec = ArchiveRecord(record_id="r1", source_collection="c1")
        r = ArchiveResult(
            records=(rec,),
            total_count=1,
            page=1,
            page_size=10,
        )
        assert len(r.records) == 1
        assert r.total_count == 1
        assert r.page_size == 10

    def test_frozen(self) -> None:
        r = ArchiveResult()
        with pytest.raises(ValueError):
            r.page = 2  # type: ignore[misc]


class TestCleanupReport:
    def test_defaults(self) -> None:
        r = CleanupReport()
        assert r.items_removed == 0
        assert r.bytes_freed == 0
        assert r.duration_ms == 0

    def test_with_data(self) -> None:
        r = CleanupReport(items_removed=42, bytes_freed=1048576, duration_ms=150)
        assert r.items_removed == 42
        assert r.bytes_freed == 1048576
        assert r.duration_ms == 150

    def test_frozen(self) -> None:
        r = CleanupReport()
        with pytest.raises(ValueError):
            r.items_removed = 10  # type: ignore[misc]
