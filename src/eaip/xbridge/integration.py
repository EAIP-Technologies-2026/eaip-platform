"""Integration layer — XBridgeRuntimeModule for kernel lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.xbridge.bridge import ConnectorBridge
from eaip.xbridge.health import XBridgeHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class XBridgeRuntimeModule:
    """RuntimeModule that bootstraps the connector bridge subsystem."""

    name: str = "xbridge"

    def __init__(self, bridge: ConnectorBridge | None = None) -> None:
        self._bridge = bridge or ConnectorBridge()
        self._log = get_logger("eaip.xbridge.integration")

    @property
    def bridge(self) -> ConnectorBridge:
        return self._bridge

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the connector bridge module."""
        self._log.info("xbridge.module.starting")
        connectors = await self._bridge.list_connectors()
        routes = await self._bridge.list_routes()
        health_check = XBridgeHealthCheck(
            connector_count=len(connectors),
            route_count=len(routes),
        )
        kernel.platform.health.register(health_check)
        self._log.info("xbridge.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the connector bridge module."""
        self._log.info("xbridge.module.stopping")


__all__ = ["XBridgeRuntimeModule"]
