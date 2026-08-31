"""Health checks for the knowledge subsystem."""

from __future__ import annotations

from typing import Any

from eaip.health.checks import HealthReport, HealthStatus
from eaip.knowledge.engine import KnowledgeEngine
from eaip.knowledge.registry import KnowledgeRegistry
from eaip.logging.context import get_logger


class KnowledgeHealthCheck:
    """Health checker for the knowledge subsystem.

    Reports the status of the vector store, embedding provider,
    and overall engine health.
    """

    name: str = "knowledge"

    def __init__(self, engine: KnowledgeEngine | KnowledgeRegistry) -> None:
        """Initialize the health check.

        Args:
            engine: The KnowledgeEngine or KnowledgeRegistry instance.
        """
        self._engine = engine
        self._log = get_logger("eaip.knowledge.health")

    async def check(self) -> HealthReport:
        """Execute a health check.

        Returns:
            A HealthReport with status information.
        """
        self._log.debug("health.check.start")

        details: dict[str, Any] = {"subsystem": "knowledge"}

        if isinstance(self._engine, KnowledgeRegistry):
            reg_health = await self._engine.health()
            details["collections"] = reg_health.get("collections", 0)
            details["documents"] = reg_health.get("documents", 0)
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
            component="knowledge",
            status=status,
            details=details,
        )

        self._log.debug("health.check.complete", status=status.value)
        return result


__all__ = ["KnowledgeHealthCheck"]
