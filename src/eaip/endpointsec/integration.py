"""Endpoint security scanner runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.endpointsec.health import EndpointSecurityHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class EndpointSecurityRuntimeModule:
    """Runtime module for endpoint security scanning."""

    name: str = "endpointsec"

    def __init__(self) -> None:
        """Initialize the endpoint security runtime module."""
        self._health_check = EndpointSecurityHealthCheck()
        self._log = get_logger("eaip.endpointsec.integration")

    @property
    def health_check(self) -> EndpointSecurityHealthCheck:
        """Return the endpoint security health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("endpointsec.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("endpointsec.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("endpointsec.module.stopping")


__all__ = ["EndpointSecurityRuntimeModule"]
