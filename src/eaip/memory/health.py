"""Health checks for the memory subsystem."""

from __future__ import annotations

from typing import Any

from eaip.health.checks import HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.memory.engine import MemoryEngine
from eaip.memory.registry import MemoryRegistry


class MemoryHealthCheck:
    """Health checker for the memory subsystem.

    Reports the status of the memory store, registry, and
    overall engine health.
    """

    name: str = "memory"

    def __init__(self, engine: MemoryEngine | MemoryRegistry) -> None:
        """Initialize the health check.

        Args:
            engine: The MemoryEngine or MemoryRegistry instance.
        """
        self._engine = engine
        self._log = get_logger("eaip.memory.health")

    async def check(self) -> HealthReport:
        """Execute a health check.

        Returns:
            A HealthReport with status information.
        """
        self._log.debug("health.check.start")

        details: dict[str, Any] = {"subsystem": "memory"}

        if isinstance(self._engine, MemoryRegistry):
            reg_health = await self._engine.health()
            details["items"] = reg_health.get("items", 0)
            details["relations"] = reg_health.get("relations", 0)
            status = HealthStatus.HEALTHY
        else:
            engine_health = await self._engine.health()
            details["engine"] = engine_health
            status = (
                HealthStatus.HEALTHY
                if engine_health.get("status") == "healthy"
                else HealthStatus.DEGRADED
            )

        result = HealthReport(
            component="memory",
            status=status,
            details=details,
        )

        self._log.debug("health.check.complete", status=status.value)
        return result


__all__ = ["MemoryHealthCheck"]
