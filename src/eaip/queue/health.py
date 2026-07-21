"""Health check for the queue subsystem."""

from __future__ import annotations

from typing import Any

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class QueueHealthCheck(HealthCheck):
    """Reports queue depths, failed message counts, and dead letter stats."""

    name: str = "eaip.queue"

    def __init__(self) -> None:
        """Initialize the health check."""
        self._queues: dict[str, Any] = {}

    def register_queue(self, queue: Any) -> None:
        """Register a queue for health monitoring."""
        key = (getattr(queue, "config", None) and queue.config.name) or str(id(queue))
        self._queues[key] = queue

    def unregister_queue(self, name: str) -> None:
        """Unregister a queue from health monitoring."""
        self._queues.pop(name, None)

    async def check(self) -> HealthReport:
        """Check queue health and return a report."""
        total_depth = 0
        total_dlq = 0
        queue_details: dict[str, object] = {}

        for name, queue in self._queues.items():
            stats = await self._get_queue_stats(queue)
            if stats is not None:
                total_depth += stats["current_depth"]
                total_dlq += stats["dead_letter_depth"]
                queue_details[name] = stats

        if total_dlq > 0:
            return HealthReport(
                component="queue",
                status=HealthStatus.DEGRADED,
                message=f"{total_dlq} message(s) in dead-letter queues",
                details={
                    "total_depth": total_depth,
                    "dead_letter_depth": total_dlq,
                    "queues": queue_details,
                },
            )

        if total_depth > 0:
            return HealthReport(
                component="queue",
                status=HealthStatus.HEALTHY,
                message=f"{total_depth} message(s) in queues",
                details={
                    "total_depth": total_depth,
                    "dead_letter_depth": total_dlq,
                    "queues": queue_details,
                },
            )

        return HealthReport(
            component="queue",
            status=HealthStatus.HEALTHY,
            message="All queues empty",
            details={
                "total_depth": total_depth,
                "dead_letter_depth": total_dlq,
                "queues": queue_details,
            },
        )

    async def _get_queue_stats(self, queue: Any) -> dict[str, int] | None:
        try:
            result = queue.get_stats()
            if hasattr(result, "__await__"):
                stats = await result
            else:
                stats = result
            if stats is None:
                return None
            return {
                "current_depth": getattr(stats, "current_depth", 0),
                "dead_letter_depth": getattr(stats, "dead_letter_depth", 0),
                "total_enqueued": getattr(stats, "total_enqueued", 0),
                "total_dequeued": getattr(stats, "total_dequeued", 0),
                "total_failed": getattr(stats, "total_failed", 0),
            }
        except Exception:
            return None
