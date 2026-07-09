"""Capability health tracking — per-capability and aggregate subsystem health."""

from __future__ import annotations

from eaip.capabilities.capability import CapabilityStatus
from eaip.capabilities.graph import CapabilityGraph
from eaip.capabilities.registry import CapabilityRegistry
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger


class CapabilityHealthCheck(HealthCheck):
    """Health check that reports capability subsystem status.

    Reports:
    - ``HEALTHY``: all capabilities ENABLED, no dependency issues.
    - ``DEGRADED``: some capabilities DISABLED or DEPRECATED.
    - ``UNHEALTHY``: unresolved required dependencies.
    """

    name: str = "capabilities"

    def __init__(self, registry: CapabilityRegistry) -> None:
        """Initialize the health check.

        Args:
            registry: The capability registry.
        """
        self._registry = registry
        self._log = get_logger("eaip.capabilities.health")

    async def check(self) -> HealthReport:
        """Run the capability health check.

        Returns:
            A HealthReport describing capability subsystem health.
        """
        all_caps = self._registry.all()
        if not all_caps:
            return HealthReport(
                component="capabilities",
                status=HealthStatus.HEALTHY,
                message="no capabilities registered",
                details={"total": 0},
            )

        total = len(all_caps)
        enabled = sum(1 for c in all_caps if c.status is CapabilityStatus.ENABLED)
        disabled = sum(1 for c in all_caps if c.status is CapabilityStatus.DISABLED)
        deprecated = sum(1 for c in all_caps if c.status is CapabilityStatus.DEPRECATED)
        registered = sum(1 for c in all_caps if c.status is CapabilityStatus.REGISTERED)

        # Build graph to check dependency health
        try:
            graph = CapabilityGraph(all_caps)
            ordered = graph.topological_sort()
            graph_healthy = True
            graph_msg = ""
        except BaseException as exc:
            graph_healthy = False
            graph_msg = str(exc)

        if not graph_healthy:
            return HealthReport(
                component="capabilities",
                status=HealthStatus.UNHEALTHY,
                message=f"capability dependency graph: {graph_msg}",
                details={
                    "total": total,
                    "enabled": enabled,
                    "disabled": disabled,
                    "deprecated": deprecated,
                    "registered": registered,
                },
            )

        if disabled > 0 or deprecated > 0:
            status = HealthStatus.DEGRADED
            msg = (
                f"{enabled}/{total} capabilities enabled "
                f"({disabled} disabled, {deprecated} deprecated)"
            )
        else:
            status = HealthStatus.HEALTHY
            msg = f"all {total} capabilities healthy"

        return HealthReport(
            component="capabilities",
            status=status,
            message=msg,
            details={
                "total": total,
                "enabled": enabled,
                "disabled": disabled,
                "deprecated": deprecated,
                "registered": registered,
                "order": [c.name for c in ordered],
            },
        )


__all__ = ["CapabilityHealthCheck"]
