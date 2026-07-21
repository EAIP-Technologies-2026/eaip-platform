"""Health check for cluster coordination."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class ClusterHealthCheck(HealthCheck):
    """Health check reporting cluster node count and leader status."""

    name: str = "eaip.cluster"

    def __init__(
        self,
        node_count: int = 0,
        leader_id: str | None = None,
    ) -> None:
        """Initialize with the current node count and optional leader id."""
        self._node_count = node_count
        self._leader_id = leader_id

    async def check(self) -> HealthReport:
        """Run the health check and return a HealthReport."""
        details = {
            "node_count": self._node_count,
            "leader": self._leader_id,
        }
        if self._leader_id is None and self._node_count > 0:
            return HealthReport(
                component="Cluster",
                status=HealthStatus.DEGRADED,
                details=details,
                message="no leader elected",
            )
        return HealthReport(
            component="Cluster",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["ClusterHealthCheck"]
