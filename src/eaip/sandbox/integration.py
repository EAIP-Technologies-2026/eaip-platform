"""Runtime module integration for the sandbox subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.sandbox.health import SandboxHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class SandboxRuntimeModule:
    name: str = "sandbox"

    def __init__(self) -> None:
        self._health_check = SandboxHealthCheck()
        self._log = get_logger("eaip.sandbox.integration")

    @property
    def health_check(self) -> SandboxHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("sandbox.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("sandbox.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("sandbox.module.stopping")


__all__ = ["SandboxRuntimeModule"]
