"""HTTP request router runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.httprouter.health import HTTPRouterHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class HTTPRouterRuntimeModule:
    name: str = "httprouter"

    def __init__(self) -> None:
        self._health_check = HTTPRouterHealthCheck()
        self._log = get_logger("eaip.httprouter.integration")

    @property
    def health_check(self) -> HTTPRouterHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("httprouter.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("httprouter.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("httprouter.module.stopping")


__all__ = ["HTTPRouterRuntimeModule"]
