"""Health checks for the semantic indexing subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.semantic_indexing.service import SemanticIndexingService


class SemanticIndexingHealthCheck:
    """Health checker for the semantic indexing subsystem."""

    name: str = "semantic_indexing"

    def __init__(self, service: SemanticIndexingService) -> None:
        """Initialize the health check.

        Args:
            service: The SemanticIndexingService instance.
        """
        self._service = service
        self._log = get_logger("eaip.semantic_indexing.health")

    async def check(self) -> HealthReport:
        """Execute a health check.

        Returns:
            A HealthReport with status information.
        """
        self._log.debug("health.check.start")

        index_count = len(self._service.list_indexes())
        details: dict[str, object] = {
            "subsystem": "semantic_indexing",
            "index_count": index_count,
        }

        status = HealthStatus.HEALTHY

        result = HealthReport(
            component="semantic_indexing",
            status=status,
            details=details,
        )

        self._log.debug("health.check.complete", status=status.value)
        return result


__all__ = ["SemanticIndexingHealthCheck"]
