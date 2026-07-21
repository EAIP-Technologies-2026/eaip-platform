"""Health checks for the Enterprise Brain subsystem."""

from __future__ import annotations

from typing import Any

from eaip.brain.enterprise_brain import EnterpriseBrain
from eaip.health.checks import HealthReport, HealthStatus
from eaip.logging.context import get_logger


class BrainHealthCheck:
    """Health checker for the Enterprise Brain subsystem.

    Reports the status of integrated knowledge, memory, context,
    and agent sources.
    """

    name: str = "brain"

    def __init__(self, brain: EnterpriseBrain) -> None:
        """Initialize the health check.

        Args:
            brain: The EnterpriseBrain instance.
        """
        self._brain = brain
        self._log = get_logger("eaip.brain.health")

    async def check(self) -> HealthReport:
        """Execute a health check.

        Returns:
            A HealthReport with status information.
        """
        self._log.debug("health.check.start")

        details: dict[str, Any] = {"subsystem": "brain"}
        try:
            health = await self._brain.health()
            details.update(health)
            status = (
                HealthStatus.HEALTHY if health.get("status") == "healthy" else HealthStatus.DEGRADED
            )
        except Exception as exc:
            self._log.warning("health.check.failed", error=str(exc))
            details["error"] = str(exc)
            status = HealthStatus.UNHEALTHY

        result = HealthReport(
            component="brain",
            status=status,
            details=details,
        )

        self._log.debug("health.check.complete", status=status.value)
        return result


__all__ = ["BrainHealthCheck"]
