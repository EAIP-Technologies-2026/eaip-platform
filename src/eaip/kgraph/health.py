"""Health checks for the knowledge graph subsystem."""

from __future__ import annotations

from typing import Any

from eaip.health.checks import HealthReport, HealthStatus
from eaip.logging.context import get_logger


class GraphHealthCheck:
    """Health checker for the Knowledge Graph runtime.

    Reports overall graph health including entity/relationship counts.
    """

    name: str = "kgraph"

    def __init__(self, graph: Any | None = None) -> None:
        """Initialize the health check.

        Args:
            graph: Optional KnowledgeGraph instance.
        """
        self._graph = graph
        self._log = get_logger("eaip.kgraph.health")

    async def check(self) -> HealthReport:
        """Execute a health check.

        Returns:
            A HealthReport with status information.
        """
        self._log.debug("health.check.start")
        details: dict[str, object] = {"subsystem": "kgraph"}

        if self._graph is not None:
            try:
                stats = await self._graph.get_stats()
                details["total_entities"] = stats.total_entities
                details["total_relationships"] = stats.total_relationships
                details["density"] = stats.density
                status = HealthStatus.HEALTHY
            except Exception as exc:
                details["error"] = str(exc)
                status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        result = HealthReport(
            component="kgraph",
            status=status,
            details=details,
        )
        self._log.debug("health.check.complete", status=status.value)
        return result


__all__ = ["GraphHealthCheck"]
