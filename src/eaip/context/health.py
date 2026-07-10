"""Health checks for the context & prompt intelligence subsystem."""

from __future__ import annotations

from typing import Any

from eaip.context.registry import PromptRegistry
from eaip.health.checks import HealthReport, HealthStatus
from eaip.logging.context import get_logger


class ContextHealthCheck:
    """Health checker for the context & prompt intelligence subsystem.

    Reports the status of the prompt registry and overall subsystem health.
    Implements the :class:`HealthCheck` protocol.
    """

    name: str = "context"

    def __init__(self, registry: PromptRegistry) -> None:
        """Initialize the health check.

        Args:
            registry: The PromptRegistry instance to monitor.
        """
        self._registry = registry
        self._log = get_logger("eaip.context.health")

    async def check(self) -> HealthReport:
        """Execute a health check.

        Returns:
            A HealthReport with status information.
        """
        self._log.debug("health.check.start")

        details: dict[str, Any] = {"subsystem": "context"}

        try:
            reg_health = await self._registry.health()
            details["prompts"] = reg_health.get("prompts", 0)
            details["status"] = reg_health.get("status", "unknown")
            status = (
                HealthStatus.HEALTHY
                if reg_health.get("status") == "healthy"
                else HealthStatus.DEGRADED
            )
        except Exception as exc:
            details["error"] = str(exc)
            status = HealthStatus.UNHEALTHY

        result = HealthReport(
            component="context",
            status=status,
            details=details,
        )

        self._log.debug("health.check.complete", status=status.value)
        return result


__all__ = ["ContextHealthCheck"]
