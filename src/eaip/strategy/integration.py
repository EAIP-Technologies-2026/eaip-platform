"""Platform integration hooks for the strategy module."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.strategy.engine import StrategicFrameworkEngine
from eaip.strategy.persistence import StrategyStore

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class StrategyRuntimeModule:
    """RuntimeModule that registers the strategy subsystem with the kernel."""

    name: str = "strategy"

    def __init__(self, engine: StrategicFrameworkEngine | None = None, event_bus: Any = None) -> None:
        self._event_bus = event_bus
        self._store = StrategyStore()
        self._engine = engine or StrategicFrameworkEngine(event_bus=event_bus, store=self._store)
        self._log = get_logger("eaip.strategy.integration")

    @property
    def engine(self) -> StrategicFrameworkEngine:
        return self._engine

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("strategy.module.start")

        kernel.platform.capabilities.register(
            Capability(
                name="strategy:framework",
                title="Strategic Framework Engine",
                status=CapabilityStatus.ENABLED,
                tags=("strategy", "framework", "psf"),
            )
        )

        kernel.register_module("strategy.engine", self._engine)
        self._log.info("strategy.module.complete", duration_s=round(time.monotonic() - t0, 3))

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("strategy.module.stop")


__all__ = ["StrategyRuntimeModule"]
