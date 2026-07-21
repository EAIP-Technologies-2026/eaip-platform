"""Federated identity runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.fedid.health import FederatedIdentityHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class FederatedIdentityRuntimeModule:
    """Runtime module for the federated identity provider."""

    name: str = "fedid"

    def __init__(self) -> None:
        """Initialize the federated identity runtime module."""
        self._health_check = FederatedIdentityHealthCheck()
        self._log = get_logger("eaip.fedid.integration")

    @property
    def health_check(self) -> FederatedIdentityHealthCheck:
        """Return the federated identity health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("fedid.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("fedid.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("fedid.module.stopping")


__all__ = ["FederatedIdentityRuntimeModule"]
