"""Tests for AutomationScheduler."""

from __future__ import annotations

import pytest

from eaip.automation.exceptions import AutomationError
from eaip.automation.scheduler import AutomationScheduler


class TestAutomationScheduler:
    @pytest.fixture
    def scheduler(self) -> AutomationScheduler:
        return AutomationScheduler()

    async def test_schedule_rule(self, scheduler) -> None:
        await scheduler.schedule_rule("rule_1", "0 9 * * 1-5")
        scheduled = await scheduler.get_scheduled("rule_1")
        assert scheduled is not None
        assert scheduled["rule_id"] == "rule_1"
        assert scheduled["cron_expression"] == "0 9 * * 1-5"

    async def test_schedule_rule_invalid_cron(self, scheduler) -> None:
        with pytest.raises(AutomationError):
            await scheduler.schedule_rule("rule_1", "invalid cron")

    async def test_schedule_multiple_rules(self, scheduler) -> None:
        await scheduler.schedule_rule("r1", "0 9 * * 1-5")
        await scheduler.schedule_rule("r2", "*/5 * * * *")
        scheduled = await scheduler.list_scheduled()
        assert len(scheduled) == 2

    async def test_unschedule_rule(self, scheduler) -> None:
        await scheduler.schedule_rule("rule_1", "0 9 * * 1-5")
        await scheduler.unschedule_rule("rule_1")
        result = await scheduler.get_scheduled("rule_1")
        assert result is None

    async def test_unschedule_nonexistent(self, scheduler) -> None:
        await scheduler.unschedule_rule("nonexistent")

    async def test_get_scheduled_nonexistent(self, scheduler) -> None:
        result = await scheduler.get_scheduled("nonexistent")
        assert result is None

    async def test_list_scheduled_empty(self, scheduler) -> None:
        scheduled = await scheduler.list_scheduled()
        assert scheduled == []

    async def test_schedule_rule_standard_cron(self, scheduler) -> None:
        await scheduler.schedule_rule("r1", "30 4 * * 0")
        scheduled = await scheduler.get_scheduled("r1")
        assert scheduled["cron_expression"] == "30 4 * * 0"

    async def test_check_due_rules_no_schedules(self, scheduler) -> None:
        due = await scheduler.check_due_rules()
        assert due == []

    async def test_check_due_rules_with_schedule(self, scheduler) -> None:
        await scheduler.schedule_rule("r1", "0 9 * * 1-5")
        due = await scheduler.check_due_rules()
        assert isinstance(due, list)

    async def test_list_scheduled_after_operations(self, scheduler) -> None:
        await scheduler.schedule_rule("r1", "0 0 * * *")
        await scheduler.schedule_rule("r2", "*/10 * * * *")
        await scheduler.unschedule_rule("r1")
        scheduled = await scheduler.list_scheduled()
        assert len(scheduled) == 1
        assert scheduled[0]["rule_id"] == "r2"
