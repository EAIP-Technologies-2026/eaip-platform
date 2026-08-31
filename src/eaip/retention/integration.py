"""Retention service runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.retention.health import RetentionHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class RetentionRuntimeModule:
    name: str = "retention"

    def __init__(self) -> None:
        self._health_check = RetentionHealthCheck()
        self._log = get_logger("eaip.retention.integration")

    @property
    def health_check(self) -> RetentionHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("retention.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("retention.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("retention.module.stopping")


__all__ = ["RetentionRuntimeModule"]
