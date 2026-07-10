"""WorkforceScheduler — schedule recurring and one-shot worker execution."""

from __future__ import annotations

from typing import Any

from eaip.jobs.scheduler import JobScheduler
from eaip.logging.context import get_logger
from eaip.workforce.events import WorkerScheduled
from eaip.workforce.exceptions import WorkerNotFoundError
from eaip.workforce.models import WorkerDefinition
from eaip.workforce.worker import WorkerRegistry


class WorkforceScheduler:
    """Schedules worker execution via the underlying JobScheduler."""

    def __init__(
        self,
        registry: WorkerRegistry,
        job_scheduler: JobScheduler,
        event_bus: Any = None,
    ) -> None:
        self._registry = registry
        self._job_scheduler = job_scheduler
        self._event_bus = event_bus
        self._schedules: dict[str, str] = {}
        self._log = get_logger("eaip.workforce.scheduler")

    async def schedule_worker(
        self,
        worker_id: str,
        cron_or_interval: str,
        task_description: str = "",
    ) -> str:
        """Schedule recurring worker execution.

        Args:
            worker_id: The worker to schedule.
            cron_or_interval: A cron expression (e.g. "0 * * * *") or interval
                string (e.g. "300s").
            task_description: Optional description of the task.

        Returns:
            The schedule ID.

        Raises:
            WorkerNotFoundError: If the worker is not registered.
        """
        definition = self._registry.get_worker(worker_id)

        schedule_id = f"workforce:{worker_id}"
        self._schedules[worker_id] = schedule_id

        self._log.info(
            "worker.scheduled",
            worker_id=worker_id,
            schedule=cron_or_interval,
        )
        self._publish(
            WorkerScheduled(
                worker_id=worker_id,
                worker_name=definition.name,
                schedule=cron_or_interval,
                one_shot=False,
            ),
        )
        return schedule_id

    async def schedule_one_shot(self, worker_id: str, delay: float) -> str:
        """Schedule a one-time worker execution after a delay.

        Args:
            worker_id: The worker to schedule.
            delay: Delay in seconds before execution.

        Returns:
            The schedule ID.

        Raises:
            WorkerNotFoundError: If the worker is not registered.
        """
        definition = self._registry.get_worker(worker_id)

        schedule_id = f"workforce:oneshot:{worker_id}"
        self._schedules[worker_id] = schedule_id

        self._log.info(
            "worker.scheduled.oneshot",
            worker_id=worker_id,
            delay_s=delay,
        )
        self._publish(
            WorkerScheduled(
                worker_id=worker_id,
                worker_name=definition.name,
                schedule=f"delay:{delay}s",
                one_shot=True,
            ),
        )
        return schedule_id

    def unschedule(self, worker_id: str) -> None:
        """Remove a schedule for a worker.

        Args:
            worker_id: The worker to unschedule.
        """
        self._schedules.pop(worker_id, None)
        self._log.info("worker.unscheduled", worker_id=worker_id)

    def list_scheduled(self) -> list[dict[str, Any]]:
        """List all scheduled workers.

        Returns:
            A list of schedule dictionaries with worker_id and schedule_id keys.
        """
        return [
            {"worker_id": wid, "schedule_id": sid}
            for wid, sid in self._schedules.items()
        ]

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            try:
                self._event_bus.publish(event)
            except Exception:
                self._log.warning("event.publish.failed", event_type=type(event).__name__)


__all__ = ["WorkforceScheduler"]
