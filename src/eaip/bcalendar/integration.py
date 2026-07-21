"""Calendar service runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.bcalendar.health import CalendarHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CalendarRuntimeModule:
    name: str = "bcalendar"

    def __init__(self) -> None:
        self._health_check = CalendarHealthCheck()
        self._log = get_logger("eaip.bcalendar.integration")

    @property
    def health_check(self) -> CalendarHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("bcalendar.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("bcalendar.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("bcalendar.module.stopping")


__all__ = ["CalendarRuntimeModule"]
