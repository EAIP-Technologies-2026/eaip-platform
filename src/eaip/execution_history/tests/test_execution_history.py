"""Tests for execution history models, events, exceptions, service, integration, and health."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from eaip.execution_history.events import (
    ExecutionHistoryAnalyticsComputed,
    ExecutionHistoryArchived,
    ExecutionHistoryCompacted,
    ExecutionHistoryExported,
    ExecutionHistoryPurged,
    ExecutionHistoryQueried,
    ExecutionRecordCreated,
    ExecutionRecordUpdated,
)
from eaip.execution_history.exceptions import (
    ExecutionHistoryArchiveError,
    ExecutionHistoryError,
    ExecutionHistoryExportError,
    ExecutionHistoryPurgeError,
    ExecutionHistoryQueryError,
    ExecutionRecordNotFoundError,
)
from eaip.execution_history.health import ExecutionHistoryHealthCheck
from eaip.execution_history.integration import ExecutionHistoryRuntimeModule
from eaip.execution_history.models import (
    ExecutionEvent,
    ExecutionEventType,
    ExecutionFilter,
    ExecutionHistoryConfig,
    ExecutionHistoryQuery,
    ExecutionHistoryResult,
    ExecutionHistoryStats,
    ExecutionRecord,
    ExecutionSpan,
    ExecutionStatus,
)
from eaip.execution_history.service import ExecutionHistoryService

# ── Models ───────────────────────────────────────────────────────────────────


class TestExecutionStatus:
    def test_values(self) -> None:
        assert ExecutionStatus.PENDING.value == "pending"
        assert ExecutionStatus.RUNNING.value == "running"
        assert ExecutionStatus.COMPLETED.value == "completed"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.CANCELLED.value == "cancelled"
        assert ExecutionStatus.SKIPPED.value == "skipped"


class TestExecutionEventType:
    def test_values(self) -> None:
        assert ExecutionEventType.STARTED.value == "started"
        assert ExecutionEventType.PROGRESS.value == "progress"
        assert ExecutionEventType.COMPLETED.value == "completed"
        assert ExecutionEventType.FAILED.value == "failed"
        assert ExecutionEventType.CANCELLED.value == "cancelled"
        assert ExecutionEventType.LOG.value == "log"


class TestExecutionRecord:
    def test_minimal(self) -> None:
        r = ExecutionRecord(id="r1", workflow_id="w1", workflow_name="test")
        assert r.status == ExecutionStatus.PENDING
        assert r.input == {}
        assert r.output == {}
        assert r.tags == ()

    def test_frozen(self) -> None:
        r = ExecutionRecord(id="r1", workflow_id="w1", workflow_name="test")
        with pytest.raises(ValidationError):
            r.status = ExecutionStatus.COMPLETED

    def test_full(self) -> None:
        now = datetime.utcnow()
        r = ExecutionRecord(
            id="r1",
            workflow_id="w1",
            workflow_name="test",
            status=ExecutionStatus.COMPLETED,
            duration_ms=1500.0,
            created_at=now,
            tags=("urgent",),
        )
        assert r.duration_ms == 1500.0
        assert "urgent" in r.tags


class TestExecutionEvent:
    def test_minimal(self) -> None:
        e = ExecutionEvent(id="e1", execution_id="r1", event_type=ExecutionEventType.LOG)
        assert e.message == ""

    def test_frozen(self) -> None:
        e = ExecutionEvent(id="e1", execution_id="r1", event_type=ExecutionEventType.STARTED)
        with pytest.raises(ValidationError):
            e.event_type = ExecutionEventType.COMPLETED


class TestExecutionSpan:
    def test_minimal(self) -> None:
        s = ExecutionSpan(name="step1", execution_id="r1")
        assert s.status == ExecutionStatus.RUNNING
        assert s.span_id == ""

    def test_with_parent(self) -> None:
        s = ExecutionSpan(name="child", execution_id="r1", parent_span_id="parent1")
        assert s.parent_span_id == "parent1"


class TestExecutionFilter:
    def test_defaults(self) -> None:
        f = ExecutionFilter()
        assert f.workflow_ids == ()
        assert f.statuses == ()
        assert f.search == ""


class TestExecutionHistoryQuery:
    def test_defaults(self) -> None:
        q = ExecutionHistoryQuery()
        assert q.offset == 0
        assert q.limit == 50
        assert q.sort_by == "created_at"
        assert q.sort_desc is True


class TestExecutionHistoryResult:
    def test_defaults(self) -> None:
        r = ExecutionHistoryResult()
        assert r.records == ()
        assert r.total == 0
        assert r.has_more is False


class TestExecutionHistoryStats:
    def test_defaults(self) -> None:
        s = ExecutionHistoryStats()
        assert s.total_executions == 0
        assert s.avg_duration_ms == 0.0


class TestExecutionHistoryConfig:
    def test_defaults(self) -> None:
        c = ExecutionHistoryConfig()
        assert c.retention_days == 90
        assert c.export_max_records == 1_000
        assert c.enable_analytics is True


# ── Events ───────────────────────────────────────────────────────────────────


class TestExecutionRecordCreated:
    def test_minimal(self) -> None:
        record = ExecutionRecord(id="r1", workflow_id="w1", workflow_name="test")
        e = ExecutionRecordCreated(record=record)
        assert e.event_type == "eaip.execution_history.record.created"
        assert e.record.id == "r1"

    def test_frozen(self) -> None:
        record = ExecutionRecord(id="r1", workflow_id="w1", workflow_name="test")
        e = ExecutionRecordCreated(record=record)
        with pytest.raises(ValidationError):
            e.record = record


class TestExecutionRecordUpdated:
    def test_minimal(self) -> None:
        e = ExecutionRecordUpdated(record_id="r1", changes={"status": "completed"})
        assert e.event_type == "eaip.execution_history.record.updated"
        assert e.changes["status"] == "completed"


class TestExecutionHistoryQueried:
    def test_minimal(self) -> None:
        e = ExecutionHistoryQueried(query={"filter": {}}, result_count=5)
        assert e.event_type == "eaip.execution_history.queried"
        assert e.result_count == 5


class TestExecutionHistoryArchived:
    def test_minimal(self) -> None:
        e = ExecutionHistoryArchived(records_archived=10, older_than_days=30)
        assert e.event_type == "eaip.execution_history.archived"
        assert e.records_archived == 10


class TestExecutionHistoryPurged:
    def test_minimal(self) -> None:
        e = ExecutionHistoryPurged(records_purged=5, older_than_days=90)
        assert e.event_type == "eaip.execution_history.purged"
        assert e.records_purged == 5


class TestExecutionHistoryExported:
    def test_minimal(self) -> None:
        e = ExecutionHistoryExported(record_count=3, format="json", destination="/tmp")
        assert e.event_type == "eaip.execution_history.exported"
        assert e.format == "json"


class TestExecutionHistoryCompacted:
    def test_minimal(self) -> None:
        e = ExecutionHistoryCompacted(records_compacted=20, duration_ms=100.0)
        assert e.event_type == "eaip.execution_history.compacted"
        assert e.records_compacted == 20


class TestExecutionHistoryAnalyticsComputed:
    def test_minimal(self) -> None:
        e = ExecutionHistoryAnalyticsComputed(stats={"total": 10})
        assert e.event_type == "eaip.execution_history.analytics_computed"
        assert e.stats["total"] == 10


# ── Exceptions ───────────────────────────────────────────────────────────────


class TestExecutionHistoryError:
    def test_is_eaip_error(self) -> None:
        err = ExecutionHistoryError("something went wrong")
        assert str(err) == "something went wrong"


class TestExecutionRecordNotFoundError:
    def test_default_code(self) -> None:
        err = ExecutionRecordNotFoundError("not found")
        assert str(err.code) == "EAIP-0003"


class TestExecutionHistoryQueryError:
    def test_with_context(self) -> None:
        err = ExecutionHistoryQueryError("query failed", context={"offset": 0})
        assert err.context["offset"] == 0


class TestExecutionHistoryArchiveError:
    def test_basic(self) -> None:
        err = ExecutionHistoryArchiveError("archive failed")
        assert "archive" in str(err)


class TestExecutionHistoryPurgeError:
    def test_basic(self) -> None:
        err = ExecutionHistoryPurgeError("purge failed")
        assert "purge" in str(err)


class TestExecutionHistoryExportError:
    def test_basic(self) -> None:
        err = ExecutionHistoryExportError("export failed")
        assert "export" in str(err)


# ── Service ──────────────────────────────────────────────────────────────────


class TestExecutionHistoryService:
    def test_create_record(self) -> None:
        svc = ExecutionHistoryService()
        record = svc.create_record("w1", "test-workflow", trigger="manual")
        assert record.workflow_id == "w1"
        assert record.trigger == "manual"
        assert record.status == ExecutionStatus.PENDING

    def test_get_record(self) -> None:
        svc = ExecutionHistoryService()
        created = svc.create_record("w1", "test")
        fetched = svc.get_record(created.id)
        assert fetched.id == created.id

    def test_get_record_not_found(self) -> None:
        svc = ExecutionHistoryService()
        with pytest.raises(ExecutionRecordNotFoundError):
            svc.get_record("nonexistent")

    def test_update_record_status(self) -> None:
        svc = ExecutionHistoryService()
        record = svc.create_record("w1", "test")
        updated = svc.update_record(record.id, status=ExecutionStatus.RUNNING)
        assert updated.status == ExecutionStatus.RUNNING
        assert updated.started_at is not None

    def test_update_record_completed(self) -> None:
        svc = ExecutionHistoryService()
        record = svc.create_record("w1", "test")
        updated = svc.update_record(
            record.id,
            status=ExecutionStatus.COMPLETED,
            output={"result": "ok"},
            duration_ms=500.0,
        )
        assert updated.status == ExecutionStatus.COMPLETED
        assert updated.output == {"result": "ok"}
        assert updated.duration_ms == 500.0
        assert updated.completed_at is not None

    def test_update_record_not_found(self) -> None:
        svc = ExecutionHistoryService()
        with pytest.raises(ExecutionRecordNotFoundError):
            svc.update_record("nonexistent", status=ExecutionStatus.COMPLETED)

    def test_query_default(self) -> None:
        svc = ExecutionHistoryService()
        svc.create_record("w1", "a")
        svc.create_record("w1", "b")
        result = svc.query(ExecutionHistoryQuery())
        assert result.total == 2

    def test_query_filter_by_workflow(self) -> None:
        svc = ExecutionHistoryService()
        svc.create_record("w1", "a")
        svc.create_record("w2", "b")
        f = ExecutionFilter(workflow_ids=("w1",))
        q = ExecutionHistoryQuery(filter=f)
        result = svc.query(q)
        assert result.total == 1
        assert result.records[0].workflow_id == "w1"

    def test_query_filter_by_status(self) -> None:
        svc = ExecutionHistoryService()
        r1 = svc.create_record("w1", "a")
        svc.update_record(r1.id, status=ExecutionStatus.COMPLETED)
        r2 = svc.create_record("w1", "b")
        svc.update_record(r2.id, status=ExecutionStatus.FAILED)
        f = ExecutionFilter(statuses=(ExecutionStatus.COMPLETED,))
        q = ExecutionHistoryQuery(filter=f)
        result = svc.query(q)
        assert result.total == 1
        assert result.records[0].status == ExecutionStatus.COMPLETED

    def test_query_search(self) -> None:
        svc = ExecutionHistoryService()
        svc.create_record("w1", "alpha-workflow")
        svc.create_record("w1", "beta-workflow")
        f = ExecutionFilter(search="alpha")
        q = ExecutionHistoryQuery(filter=f)
        result = svc.query(q)
        assert result.total == 1

    def test_archive(self) -> None:
        svc = ExecutionHistoryService()
        old_record = ExecutionRecord(
            id="old",
            workflow_id="w1",
            workflow_name="old",
            created_at=datetime.utcnow() - timedelta(days=100),
        )
        svc._records["old"] = old_record
        svc.create_record("w1", "new")
        count = svc.archive(older_than_days=30)
        assert count == 1
        assert "old" not in svc._records

    def test_purge(self) -> None:
        svc = ExecutionHistoryService()
        old_record = ExecutionRecord(
            id="old",
            workflow_id="w1",
            workflow_name="old",
            created_at=datetime.utcnow() - timedelta(days=200),
        )
        svc._records["old"] = old_record
        svc.create_record("w1", "new")
        count = svc.purge(older_than_days=90)
        assert count == 1
        assert "old" not in svc._records

    def test_export_json(self) -> None:
        svc = ExecutionHistoryService()
        svc.create_record("w1", "test")
        count = svc.export(format="json", destination="/tmp")
        assert count == 1

    def test_export_csv(self) -> None:
        svc = ExecutionHistoryService()
        svc.create_record("w1", "test")
        count = svc.export(format="csv", destination="/tmp")
        assert count == 1

    def test_compute_analytics(self) -> None:
        svc = ExecutionHistoryService()
        r1 = svc.create_record("w1", "a")
        svc.update_record(r1.id, status=ExecutionStatus.COMPLETED, duration_ms=100.0)
        r2 = svc.create_record("w1", "b")
        svc.update_record(r2.id, status=ExecutionStatus.COMPLETED, duration_ms=200.0)
        r3 = svc.create_record("w1", "c")
        svc.update_record(r3.id, status=ExecutionStatus.FAILED)
        stats = svc.compute_analytics()
        assert stats.total_executions == 3
        assert stats.completed == 2
        assert stats.failed == 1
        assert stats.avg_duration_ms == 150.0

    def test_compact(self) -> None:
        svc = ExecutionHistoryService()
        old = ExecutionRecord(
            id="old",
            workflow_id="w1",
            workflow_name="old",
            completed_at=datetime.utcnow() - timedelta(days=200),
        )
        svc._records["old"] = old
        svc.create_record("w1", "new")
        count = svc.compact()
        assert count == 1


# ── Integration ──────────────────────────────────────────────────────────────


class TestExecutionHistoryRuntimeModule:
    def test_module_name(self) -> None:
        module = ExecutionHistoryRuntimeModule()
        assert module.name == "execution_history"

    def test_default_config(self) -> None:
        module = ExecutionHistoryRuntimeModule()
        assert module.config.retention_days == 90

    def test_custom_config(self) -> None:
        config = ExecutionHistoryConfig(retention_days=45)
        module = ExecutionHistoryRuntimeModule(config=config)
        assert module.config.retention_days == 45

    def test_service_property(self) -> None:
        module = ExecutionHistoryRuntimeModule()
        assert module.service is not None

    @pytest.mark.asyncio
    async def test_start_stop(self) -> None:
        module = ExecutionHistoryRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)
        kernel.platform.capabilities.register.assert_called_once()
        kernel.platform.health.register.assert_called_once()

        await module.stop(kernel)


# ── Health ───────────────────────────────────────────────────────────────────


class TestExecutionHistoryHealthCheck:
    @pytest.mark.asyncio
    async def test_check_healthy(self) -> None:
        service = ExecutionHistoryService()
        service.create_record("w1", "test")
        check = ExecutionHistoryHealthCheck(service=service)
        report = await check.check()
        assert report.component == "execution_history"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_check_degraded(self) -> None:
        service = ExecutionHistoryService()
        check = ExecutionHistoryHealthCheck(service=service)
        report = await check.check()
        assert report.status.value == "degraded"
