"""RuntimeKernel integration — registers GoalEngine as a RuntimeModule."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.goals.engine import GoalEngine
from eaip.goals.health import GoalHealthCheck
from eaip.goals.tracker import GoalTracker
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class GoalRuntimeModule:
    """RuntimeModule that registers the goal subsystem with the kernel.

    On startup:
      - Creates GoalTracker and GoalEngine.
      - Registers GoalHealthCheck.
      - Registers goals capability.

    On shutdown:
      - Cleans up resources.
    """

    name: str = "goals"

    def __init__(
        self,
        engine: GoalEngine | None = None,
        tracker: GoalTracker | None = None,
        event_bus: Any = None,
        workforce_orchestrator: Any = None,
    ) -> None:
        self._event_bus = event_bus
        self._tracker = tracker or GoalTracker()
        self._engine = engine or GoalEngine(
            tracker=self._tracker,
            event_bus=event_bus,
            workforce_orchestrator=workforce_orchestrator,
        )
        self._health_check = GoalHealthCheck()
        self._log = get_logger("eaip.goals.integration")

    @property
    def engine(self) -> GoalEngine:
        return self._engine

    @property
    def tracker(self) -> GoalTracker:
        return self._tracker

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("goals.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(Capability(
            name="goals:engine",
            title="Business Goal Engine",
            status=CapabilityStatus.ENABLED,
            tags=("goals", "engine"),
        ))

        kernel.register_module("goals.engine", self._engine)
        kernel.register_module("goals.tracker", self._tracker)

        self._log.info(
            "goals.module.complete",
            duration_s=round(time.monotonic() - t0, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("goals.module.stop")


__all__ = ["GoalRuntimeModule"]
