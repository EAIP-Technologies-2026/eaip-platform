from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from eaip.logging.context import get_logger


class PipelineScheduler:
    def __init__(self) -> None:
        self._log = get_logger("eaip.datapipeline.scheduler")
        self._schedules: dict[str, dict[str, Any]] = {}

    async def schedule_pipeline(self, pipeline_id: str, cron_expression: str) -> None:
        from croniter import croniter

        if not croniter.is_valid(cron_expression):
            raise ValueError(f"Invalid cron expression: {cron_expression!r}")

        self._schedules[pipeline_id] = {
            "pipeline_id": pipeline_id,
            "cron_expression": cron_expression,
            "next_run": croniter(cron_expression, datetime.now(UTC)).get_next(datetime),
        }
        self._log.info(
            "pipeline.scheduled",
            pipeline_id=pipeline_id,
            cron=cron_expression,
        )

    async def unschedule_pipeline(self, pipeline_id: str) -> None:
        self._schedules.pop(pipeline_id, None)
        self._log.info("pipeline.unscheduled", pipeline_id=pipeline_id)

    async def check_due_pipelines(self) -> list[str]:
        from croniter import croniter

        now = datetime.now(UTC)
        due: list[str] = []

        for pipeline_id, schedule in list(self._schedules.items()):
            next_run = schedule["next_run"]
            if next_run <= now:
                due.append(pipeline_id)
                cron = croniter(schedule["cron_expression"], now)
                schedule["next_run"] = cron.get_next(datetime)

        return due

    async def get_scheduled(self, pipeline_id: str) -> dict[str, Any] | None:
        return self._schedules.get(pipeline_id)

    async def list_scheduled(self) -> list[dict[str, Any]]:
        return list(self._schedules.values())


__all__ = ["PipelineScheduler"]
