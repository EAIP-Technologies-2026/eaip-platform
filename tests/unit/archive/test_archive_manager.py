"""Tests for ArchiveManager."""

from __future__ import annotations

import pytest

from eaip.archive.exceptions import ArchiveNotFoundError
from eaip.archive.manager import ArchiveManager
from eaip.archive.models import (
    ArchiveConfig,
    ArchiveQuery,
    RetentionPolicy,
)


class TestArchiveManager:
    def test_create_archive(self) -> None:
        mgr = ArchiveManager()
        record = mgr.create_archive(
            record_id="rec_1",
            source_collection="orders",
            data=b"order data",
            checksum="abc123",
            metadata={"env": "test"},
        )
        assert record.record_id == "rec_1"
        assert record.source_collection == "orders"
        assert record.size_bytes == 10
        assert record.checksum == "abc123"
        assert record.metadata == {"env": "test"}

    def test_create_archive_auto_checksum(self) -> None:
        mgr = ArchiveManager()
        record = mgr.create_archive("rec_1", "orders", b"data")
        assert record.checksum != ""

    def test_restore_existing(self) -> None:
        mgr = ArchiveManager()
        mgr.create_archive("rec_1", "orders", b"hello world")
        data = mgr.restore("rec_1")
        assert data == b"hello world"

    def test_restore_missing(self) -> None:
        mgr = ArchiveManager()
        with pytest.raises(ArchiveNotFoundError):
            mgr.restore("nonexistent")

    def test_query_by_source_collection(self) -> None:
        mgr = ArchiveManager()
        mgr.create_archive("r1", "orders", b"data1")
        mgr.create_archive("r2", "invoices", b"data2")
        result = mgr.query(ArchiveQuery(filters={"source_collection": "orders"}))
        assert result.total_count == 1
        assert result.records[0].record_id == "r1"

    def test_query_by_record_id(self) -> None:
        mgr = ArchiveManager()
        mgr.create_archive("r1", "orders", b"data1")
        result = mgr.query(ArchiveQuery(filters={"record_id": "r1"}))
        assert result.total_count == 1
        assert result.records[0].record_id == "r1"

    def test_query_pagination(self) -> None:
        mgr = ArchiveManager()
        for i in range(10):
            mgr.create_archive(f"r{i}", "orders", b"x")
        result = mgr.query(ArchiveQuery(limit=3, offset=2))
        assert result.total_count == 10
        assert len(result.records) == 3
        assert result.page == 1
        assert result.page_size == 3

    def test_query_no_match(self) -> None:
        mgr = ArchiveManager()
        mgr.create_archive("r1", "orders", b"data")
        result = mgr.query(ArchiveQuery(filters={"source_collection": "nonexistent"}))
        assert result.total_count == 0
        assert result.records == ()

    def test_add_and_apply_retention_policy(self) -> None:
        mgr = ArchiveManager()
        mgr.create_archive("r1", "orders", b"data")
        policy = RetentionPolicy(
            policy_id="p1",
            name="Test policy",
            max_age_days=0,
            max_size_bytes=1,
            action="delete",
            priority=1,
        )
        mgr.add_policy(policy)
        affected = mgr.apply_retention_policy("p1")
        assert affected == 1

    def test_remove_policy(self) -> None:
        mgr = ArchiveManager()
        policy = RetentionPolicy(policy_id="p1", name="N")
        mgr.add_policy(policy)
        mgr.remove_policy("p1")
        with pytest.raises(ArchiveNotFoundError):
            mgr.apply_retention_policy("p1")

    def test_run_cleanup(self) -> None:
        mgr = ArchiveManager()
        mgr.create_archive("r1", "orders", b"x" * 100)
        policy = RetentionPolicy(
            policy_id="p1",
            name="Small limit",
            max_size_bytes=10,
            action="delete",
            priority=10,
        )
        mgr.add_policy(policy)
        report = mgr.run_cleanup()
        assert report.items_removed == 1
        assert report.duration_ms >= 0

    def test_config_default(self) -> None:
        mgr = ArchiveManager()
        assert isinstance(mgr.config, ArchiveConfig)
        assert mgr.config.storage_backend == "local"

    def test_config_custom(self) -> None:
        config = ArchiveConfig(storage_backend="s3")
        mgr = ArchiveManager(config=config)
        assert mgr.config.storage_backend == "s3"
