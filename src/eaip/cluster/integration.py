"""Runtime module integration for cluster coordination."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.cluster.coordinator import ClusterCoordinator
from eaip.cluster.health import ClusterHealthCheck
from eaip.cluster.models import ClusterConfig
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ClusterRuntimeModule:
    """Runtime module that registers the cluster capability and health check."""

    name: str = "cluster"

    def __init__(
        self,
        config: ClusterConfig | None = None,
        coordinator: ClusterCoordinator | None = None,
    ) -> None:
        """Initialize with optional config and coordinator."""
        self._config = config or ClusterConfig(cluster_name="default")
        self._coordinator = coordinator or ClusterCoordinator(config=self._config)
        self._log = get_logger("eaip.cluster.integration")

    @property
    def coordinator(self) -> ClusterCoordinator:
        """Return the underlying cluster coordinator."""
        return self._coordinator

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the cluster capability and health check with the kernel."""
        self._log.info("cluster.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.cluster",
            title="Cluster Coordination & High Availability",
            description=(
                "Cluster node coordination, leader election, "
                "heartbeat monitoring, and high availability"
            ),
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=(
                "cluster",
                "coordination",
                "ha",
                "election",
                "heartbeat",
            ),
        )
        platform.capabilities.register(capability)
        platform.health.register(ClusterHealthCheck())
        self._log.info("cluster.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Gracefully stop the cluster module."""
        self._log.info("cluster.module.stopping")


__all__ = ["ClusterRuntimeModule"]
