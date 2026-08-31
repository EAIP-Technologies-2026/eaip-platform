"""Git integration runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.gitsvc.health import GitServiceHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class GitServiceRuntimeModule:
    name: str = "gitsvc"

    def __init__(self) -> None:
        self._health_check = GitServiceHealthCheck()
        self._log = get_logger("eaip.gitsvc.integration")

    @property
    def health_check(self) -> GitServiceHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("gitsvc.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("gitsvc.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("gitsvc.module.stopping")


__all__ = ["GitServiceRuntimeModule"]
