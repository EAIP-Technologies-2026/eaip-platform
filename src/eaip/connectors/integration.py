"""Integration layer — ConnectorRuntimeModule for kernel lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.connectors.health import ConnectorHealthCheck
from eaip.connectors.service import ConnectorService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ConnectorRuntimeModule:
    """RuntimeModule that bootstraps the connector management subsystem."""

    name: str = "connectors"

    def __init__(self, service: ConnectorService | None = None) -> None:
        """Initialize the runtime module."""
        self._service = service or ConnectorService()
        self._log = get_logger("eaip.connectors.integration")

    @property
    def service(self) -> ConnectorService:
        """Return the underlying connector service."""
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the connector management module."""
        self._log.info("connectors.module.starting")
        entries = await self._service.list()
        health_check = ConnectorHealthCheck(connector_count=len(entries))
        kernel.platform.health.register(health_check)
        self._log.info("connectors.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the connector management module."""
        self._log.info("connectors.module.stopping")


__all__ = ["ConnectorRuntimeModule"]
