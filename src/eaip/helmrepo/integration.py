"""Helm chart repository runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.helmrepo.health import HelmChartHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class HelmChartRuntimeModule:
    name: str = "helmrepo"

    def __init__(self) -> None:
        self._health_check = HelmChartHealthCheck()
        self._log = get_logger("eaip.helmrepo.integration")

    @property
    def health_check(self) -> HelmChartHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("helmrepo.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("helmrepo.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("helmrepo.module.stopping")


__all__ = ["HelmChartRuntimeModule"]
