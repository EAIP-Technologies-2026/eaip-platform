"""Automation scheduler - cron-based rule scheduling via croniter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from eaip.automation.events import ScheduleTriggered
from eaip.automation.exceptions import AutomationError
from eaip.automation.models import TriggerEvent
from eaip.events.bus import EventBus
from eaip.jobs.models import CronExpression
from eaip.logging.context import get_logger


class _ScheduleEntry:
    def __init__(
        self, rule_id: str, cron_expression: str, last_checked: datetime | None = None
    ) -> None:
        self.rule_id = rule_id
        self.cron_expression = cron_expression
        self.last_checked = last_checked


class AutomationScheduler:
    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus or EventBus()
        self._log = get_logger("eaip.automation.scheduler")
        self._schedules: dict[str, _ScheduleEntry] = {}

    async def schedule_rule(self, rule_id: str, cron_expression: str) -> None:
        try:
            parsed = CronExpression.from_string(cron_expression)
            parsed.to_cron_string()
        except ValueError as exc:
            raise AutomationError(
                f"Invalid cron expression {cron_expression!r}: {exc}",
                context={"rule_id": rule_id, "cron_expression": cron_expression},
            )

        self._schedules[rule_id] = _ScheduleEntry(
            rule_id=rule_id,
            cron_expression=cron_expression,
        )
        self._log.info(
            "schedule.registered",
            rule_id=rule_id,
            cron_expression=cron_expression,
        )

    async def unschedule_rule(self, rule_id: str) -> None:
        self._schedules.pop(rule_id, None)
        self._log.info("schedule.unregistered", rule_id=rule_id)

    async def check_due_rules(self) -> list[TriggerEvent]:
        due_events: list[TriggerEvent] = []
        now = datetime.now(UTC)

        for rule_id, entry in list(self._schedules.items()):
            try:
                parsed = CronExpression.from_string(entry.cron_expression)
                parts = [
                    parsed.minute,
                    parsed.hour,
                    parsed.day_of_month,
                    parsed.month,
                    parsed.day_of_week,
                ]
                from croniter import croniter

                base = now if entry.last_checked is None else entry.last_checked

                cron = croniter(" ".join(parts), base)
                next_time = cron.get_next(datetime)

                if next_time <= now:
                    trigger = TriggerEvent(
                        id=f"schedule-{rule_id}-{now.timestamp():.0f}",
                        type="automation.schedule.triggered",
                        source="automation.scheduler",
                        timestamp=now,
                        payload={"rule_id": rule_id, "cron": entry.cron_expression},
                        correlation_id="",
                        metadata={},
                    )
                    due_events.append(trigger)
                    entry.last_checked = now

                    await self._event_bus.publish(
                        ScheduleTriggered(rule_id=rule_id, cron_expression=entry.cron_expression),
                    )
            except Exception as exc:
                self._log.error(
                    "schedule.check.failed",
                    rule_id=rule_id,
                    error=str(exc),
                )

        return due_events

    async def get_scheduled(self, rule_id: str) -> dict[str, Any] | None:
        entry = self._schedules.get(rule_id)
        if entry is None:
            return None
        return {
            "rule_id": entry.rule_id,
            "cron_expression": entry.cron_expression,
            "last_checked": entry.last_checked,
        }

    async def list_scheduled(self) -> list[dict[str, Any]]:
        return [
            {
                "rule_id": entry.rule_id,
                "cron_expression": entry.cron_expression,
                "last_checked": entry.last_checked,
            }
            for entry in self._schedules.values()
        ]


__all__ = ["AutomationScheduler"]
