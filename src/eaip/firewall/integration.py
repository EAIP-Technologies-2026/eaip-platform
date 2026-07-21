"""Firewall rule manager runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.firewall.health import FirewallHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class FirewallRuntimeModule:
    """Runtime module for firewall rule management."""

    name: str = "firewall"

    def __init__(self) -> None:
        self._health_check = FirewallHealthCheck()
        self._log = get_logger("eaip.firewall.integration")

    @property
    def health_check(self) -> FirewallHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("firewall.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("firewall.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("firewall.module.stopping")


__all__ = ["FirewallRuntimeModule"]
