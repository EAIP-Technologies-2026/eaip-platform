"""External identity mapper runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.extidmap.health import ExternalIdentityHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ExternalIdentityRuntimeModule:
    """Runtime module for external identity mapping."""

    name: str = "extidmap"

    def __init__(self) -> None:
        self._health_check = ExternalIdentityHealthCheck()
        self._log = get_logger("eaip.extidmap.integration")

    @property
    def health_check(self) -> ExternalIdentityHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("extidmap.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("extidmap.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("extidmap.module.stopping")


__all__ = ["ExternalIdentityRuntimeModule"]
