"""Runtime module integration for the config drift subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.configdrift.health import ConfigDriftHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ConfigDriftRuntimeModule:
    name: str = "configdrift"

    def __init__(self) -> None:
        self._health_check = ConfigDriftHealthCheck()
        self._log = get_logger("eaip.configdrift.integration")

    @property
    def health_check(self) -> ConfigDriftHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("configdrift.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("configdrift.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("configdrift.module.stopping")


__all__ = ["ConfigDriftRuntimeModule"]
