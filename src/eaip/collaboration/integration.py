"""RuntimeKernel integration — registers CollaborationRuntime as a RuntimeModule."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.collaboration.approval import CollaborationApprovalService
from eaip.collaboration.coordinator import CoordinationEngine
from eaip.collaboration.delegation import TaskDelegationService
from eaip.collaboration.health import CollaborationHealthCheck
from eaip.collaboration.state import SharedStateManager
from eaip.collaboration.tracking import ExecutionTracker
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CollaborationRuntimeModule:
    """RuntimeModule that registers the collaboration subsystem with the kernel.

    On startup:
      - Creates CoordinationEngine, TaskDelegationService,
        CollaborationApprovalService, SharedStateManager, ExecutionTracker.
      - Registers CollaborationHealthCheck.
      - Registers collaboration capability.

    On shutdown:
      - Cleans up resources.
    """

    name: str = "collaboration"

    def __init__(
        self,
        agent_runtime: Any = None,
        event_bus: Any = None,
    ) -> None:
        self._event_bus = event_bus
        self._coordinator = CoordinationEngine(
            agent_runtime=agent_runtime,
            event_bus=event_bus,
        )
        self._delegation = TaskDelegationService(event_bus=event_bus)
        self._approval = CollaborationApprovalService(event_bus=event_bus)
        self._state_manager = SharedStateManager(event_bus=event_bus)
        self._tracker = ExecutionTracker()
        self._health_check = CollaborationHealthCheck()
        self._log = get_logger("eaip.collaboration.integration")

    @property
    def coordinator(self) -> CoordinationEngine:
        return self._coordinator

    @property
    def delegation(self) -> TaskDelegationService:
        return self._delegation

    @property
    def approval(self) -> CollaborationApprovalService:
        return self._approval

    @property
    def state_manager(self) -> SharedStateManager:
        return self._state_manager

    @property
    def tracker(self) -> ExecutionTracker:
        return self._tracker

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("collaboration.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="collaboration:runtime",
                title="Collaboration & Workflow Runtime",
                status=CapabilityStatus.ENABLED,
                tags=("collaboration", "runtime", "workflow"),
            )
        )

        kernel.register_module("collaboration.coordinator", self._coordinator)
        kernel.register_module("collaboration.delegation", self._delegation)
        kernel.register_module("collaboration.approval", self._approval)
        kernel.register_module("collaboration.state", self._state_manager)
        kernel.register_module("collaboration.tracker", self._tracker)

        self._log.info(
            "collaboration.module.complete",
            duration_s=round(time.monotonic() - t0, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("collaboration.module.stop")


__all__ = ["CollaborationRuntimeModule"]
