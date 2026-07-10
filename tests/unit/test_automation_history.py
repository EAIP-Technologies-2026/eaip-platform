"""Tests for ExecutionHistory."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from eaip.automation.history import ExecutionHistory
from eaip.automation.models import (
    AutomationExecution,
    AutomationStatus,
    TriggerType,
)


class TestExecutionHistory:
    @pytest.fixture
    def history(self) -> ExecutionHistory:
        return ExecutionHistory()

    @pytest.fixture
    def sample_execution(self) -> AutomationExecution:
        return AutomationExecution(
            id="exec_1",
            rule_id="rule_1",
            rule_name="Test Rule",
            trigger_type=TriggerType.MANUAL,
            status=AutomationStatus.COMPLETED,
            duration_ms=1000.0,
            result="success",
        )

    async def test_record_execution(self, history, sample_execution) -> None:
        await history.record_execution(sample_execution)
        detail = await history.get_execution_detail("exec_1")
        assert detail is not None
        assert detail.id == "exec_1"

    async def test_get_history_all(self, history) -> None:
        e1 = AutomationExecution(id="e1", rule_id="r1", trigger_type=TriggerType.MANUAL, status=AutomationStatus.COMPLETED)
        e2 = AutomationExecution(id="e2", rule_id="r2", trigger_type=TriggerType.MANUAL, status=AutomationStatus.FAILED)
        await history.record_execution(e1)
        await history.record_execution(e2)
        entries = await history.get_history()
        assert len(entries) == 2

    async def test_get_history_by_rule_id(self, history) -> None:
        e1 = AutomationExecution(id="e1", rule_id="r1", trigger_type=TriggerType.MANUAL)
        e2 = AutomationExecution(id="e2", rule_id="r2", trigger_type=TriggerType.MANUAL)
        await history.record_execution(e1)
        await history.record_execution(e2)
        entries = await history.get_history(rule_id="r1")
        assert len(entries) == 1
        assert entries[0].rule_id == "r1"

    async def test_get_history_by_status(self, history) -> None:
        e1 = AutomationExecution(id="e1", rule_id="r1", trigger_type=TriggerType.MANUAL, status=AutomationStatus.COMPLETED)
        e2 = AutomationExecution(id="e2", rule_id="r1", trigger_type=TriggerType.MANUAL, status=AutomationStatus.FAILED)
        await history.record_execution(e1)
        await history.record_execution(e2)
        entries = await history.get_history(status=AutomationStatus.COMPLETED)
        assert len(entries) == 1

    async def test_get_history_limit(self, history) -> None:
        for i in range(5):
            e = AutomationExecution(id=f"e{i}", rule_id="r1", trigger_type=TriggerType.MANUAL)
            await history.record_execution(e)
        entries = await history.get_history(limit=3)
        assert len(entries) == 3

    async def test_get_execution_detail_missing(self, history) -> None:
        detail = await history.get_execution_detail("nonexistent")
        assert detail is None

    async def test_cleanup_history(self, history) -> None:
        old = AutomationExecution(
            id="old_exec",
            rule_id="r1",
            trigger_type=TriggerType.MANUAL,
            started_at=datetime.now(timezone.utc) - timedelta(days=60),
        )
        new = AutomationExecution(
            id="new_exec",
            rule_id="r1",
            trigger_type=TriggerType.MANUAL,
        )
        await history.record_execution(old)
        await history.record_execution(new)
        removed = await history.cleanup_history(retention_days=30)
        assert removed == 1
        entries = await self.get_history(history)
        assert len(entries) == 1

    async def get_history(self, history) -> list:
        return await history.get_history()

    async def test_cleanup_history_no_removal(self, history) -> None:
        e = AutomationExecution(
            id="recent",
            rule_id="r1",
            trigger_type=TriggerType.MANUAL,
        )
        await history.record_execution(e)
        removed = await history.cleanup_history(retention_days=30)
        assert removed == 0

    async def test_get_statistics_empty(self, history) -> None:
        stats = await history.get_statistics()
        assert stats["total"] == 0
        assert stats["success_rate"] == 0.0

    async def test_get_statistics(self, history) -> None:
        await history.record_execution(
            AutomationExecution(id="e1", rule_id="r1", trigger_type=TriggerType.MANUAL, status=AutomationStatus.COMPLETED, duration_ms=100.0),
        )
        await history.record_execution(
            AutomationExecution(id="e2", rule_id="r1", trigger_type=TriggerType.MANUAL, status=AutomationStatus.COMPLETED, duration_ms=200.0),
        )
        await history.record_execution(
            AutomationExecution(id="e3", rule_id="r1", trigger_type=TriggerType.MANUAL, status=AutomationStatus.FAILED, duration_ms=50.0),
        )
        stats = await history.get_statistics()
        assert stats["total"] == 3
        assert stats["completed"] == 2
        assert stats["failed"] == 1
        assert stats["success_rate"] == pytest.approx(66.6667, rel=0.1)

    async def test_get_statistics_by_rule(self, history) -> None:
        await history.record_execution(
            AutomationExecution(id="e1", rule_id="r1", trigger_type=TriggerType.MANUAL, status=AutomationStatus.COMPLETED),
        )
        await history.record_execution(
            AutomationExecution(id="e2", rule_id="r2", trigger_type=TriggerType.MANUAL, status=AutomationStatus.COMPLETED),
        )
        stats = await history.get_statistics(rule_id="r1")
        assert stats["total"] == 1
        assert stats["completed"] == 1
