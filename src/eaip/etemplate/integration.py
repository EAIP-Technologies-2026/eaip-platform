"""Template engine runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.etemplate.health import TemplateEngineHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class TemplateEngineRuntimeModule:
    name: str = "etemplate"

    def __init__(self) -> None:
        self._health_check = TemplateEngineHealthCheck()
        self._log = get_logger("eaip.etemplate.integration")

    @property
    def health_check(self) -> TemplateEngineHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("etemplate.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("etemplate.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("etemplate.module.stopping")


__all__ = ["TemplateEngineRuntimeModule"]
