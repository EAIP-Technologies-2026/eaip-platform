"""Cost engine runtime module — wires CostTracker, BudgetManager, AlertService, etc."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from eaip.cost.alerts import AlertService
from eaip.cost.budgets import BudgetManager
from eaip.cost.health import CostHealthCheck
from eaip.cost.optimizer import CostOptimizer
from eaip.cost.reporting import CostReportingService
from eaip.cost.tracker import CostTracker

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CostRuntimeModule:
    """Runtime module that registers cost engine services.

    Implements the :class:`eaip.runtime.module.RuntimeModule` protocol.
    """

    name: str = "cost"

    def __init__(self) -> None:
        self.tracker = CostTracker()
        self.alert_service = AlertService()
        self.budget_manager = BudgetManager(self.tracker, self.alert_service)
        self.optimizer = CostOptimizer(self.tracker)
        self.reporting = CostReportingService(self.tracker)
        self.health_check = CostHealthCheck(self.tracker, self.budget_manager, self.alert_service)

    async def start(self, kernel: RuntimeKernel) -> None:
        kernel.register_module("cost.tracker", self.tracker)
        kernel.register_module("cost.budget_manager", self.budget_manager)
        kernel.register_module("cost.alert_service", self.alert_service)
        kernel.register_module("cost.optimizer", self.optimizer)
        kernel.register_module("cost.reporting", self.reporting)

        # wire event callbacks to emit domain events
        async def _event_forward(record: Any) -> None:
            with contextlib.suppress(Exception):
                await kernel.platform.events.publish(record)

        self.tracker.set_event_callback(_event_forward)

    async def stop(self, kernel: RuntimeKernel) -> None:
        pass
