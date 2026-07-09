"""Runtime integration — CapabilityRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.capabilities.capability import CapabilityStatus
from eaip.capabilities.discovery import CapabilityDiscovery
from eaip.capabilities.graph import CapabilityGraph
from eaip.capabilities.health import CapabilityHealthCheck
from eaip.capabilities.registry import CapabilityRegistry
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CapabilityRuntimeModule:
    """RuntimeModule that manages capabilities during kernel boot.

    - On start: discovers capabilities from installed plugins, validates
      the dependency graph, registers capability health checks.
    - On stop: marks all capabilities as DISABLED.
    """

    name: str = "capabilities"

    def __init__(
        self,
        registry: CapabilityRegistry,
        discovery: CapabilityDiscovery | None = None,
    ) -> None:
        """Initialize the CapabilityRuntimeModule.

        Args:
            registry: The capability registry.
            discovery: Optional capability discovery service.
        """
        self._registry = registry
        self._discovery = discovery or CapabilityDiscovery()
        self._log = get_logger("eaip.runtime.capability_integration")
        self._startup_duration: float = 0.0

    @property
    def startup_duration(self) -> float:
        """Return the last capability startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel) -> None:
        """Discover capabilities and validate their dependency graph.

        Args:
            kernel: The runtime kernel.
        """
        self._log.info("capability.module.start")
        t0 = time.monotonic()

        plugins = kernel.platform.plugin_loader.all()
        discovered = self._discovery.discover_from_plugins(plugins, self._registry)
        self._log.info(
            "capability.module.discovered",
            count=len(discovered),
        )

        all_caps = self._registry.all()
        if all_caps:
            try:
                graph = CapabilityGraph(all_caps)
                ordered = graph.topological_sort()
                self._log.info(
                    "capability.module.graph_valid",
                    count=len(all_caps),
                    order=[c.name for c in ordered],
                )

                for cap in ordered:
                    if cap.status is CapabilityStatus.REGISTERED:
                        self._registry.enable(cap.name)
                        self._log.info(
                            "capability.module.enabled",
                            capability=cap.name,
                        )
            except BaseException as exc:
                self._log.error(
                    "capability.module.graph_failed",
                    error=repr(exc),
                )

        check = CapabilityHealthCheck(self._registry)
        kernel.platform.health.register(check)

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "capability.module.complete",
            registered=len(all_caps),
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Disable all capabilities during shutdown.

        Args:
            _kernel: The runtime kernel.
        """
        self._log.info("capability.module.stop")
        for cap in self._registry.all():
            if cap.status is CapabilityStatus.ENABLED:
                self._registry.disable(cap.name)
        self._log.info("capability.module.stopped")


__all__ = ["CapabilityRuntimeModule"]
