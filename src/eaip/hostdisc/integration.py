"""Host discovery runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.hostdisc.health import HostDiscoveryHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class HostDiscoveryRuntimeModule:
    name: str = "hostdisc"

    def __init__(self) -> None:
        self._health_check = HostDiscoveryHealthCheck()
        self._log = get_logger("eaip.hostdisc.integration")

    @property
    def health_check(self) -> HostDiscoveryHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("hostdisc.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("hostdisc.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("hostdisc.module.stopping")


__all__ = ["HostDiscoveryRuntimeModule"]
