"""RuntimeKernel integration — registers AiCostService as a RuntimeModule."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from eaip.ai_cost.health import AiCostHealthCheck
from eaip.ai_cost.service import AiCostService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AiCostRuntimeModule:
    """Runtime module that registers AI cost optimization services.

    Implements the :class:`eaip.runtime.module.RuntimeModule` protocol.
    """

    name: str = "ai_cost"

    def __init__(self, service: AiCostService | None = None) -> None:
        self._service = service or AiCostService()
        self._health_check = AiCostHealthCheck(service=self._service)
        self._log = get_logger("eaip.ai_cost.integration")

    @property
    def service(self) -> AiCostService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("ai_cost.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.register_module("ai_cost.service", self._service)

        async def _event_forward(record: Any) -> None:
            with contextlib.suppress(Exception):
                await kernel.platform.events.publish(record)

        self._service.set_event_callback(_event_forward)

        self._log.info("ai_cost.module.complete")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("ai_cost.module.stop")


__all__ = ["AiCostRuntimeModule"]
