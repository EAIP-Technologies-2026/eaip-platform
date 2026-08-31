"""Runtime integration — AgentGovernanceRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.agent_governance.health import AgentGovernanceHealthCheck
from eaip.agent_governance.service import AgentGovernanceService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AgentGovernanceRuntimeModule:
    """RuntimeModule that manages agent governance during kernel boot.

    - On start: initialises the governance service and registers health checks.
    - On stop: disables all governance policies.
    """

    name: str = "agent_governance"

    def __init__(
        self,
        service: AgentGovernanceService | None = None,
    ) -> None:
        """Initialize the AgentGovernanceRuntimeModule.

        Args:
            service: Optional governance service. Creates a new one if not provided.
        """
        self._service = service or AgentGovernanceService()
        self._log = get_logger("eaip.runtime.agent_governance_integration")
        self._startup_duration: float = 0.0

    @property
    def startup_duration(self) -> float:
        """Return the last governance startup duration in seconds."""
        return self._startup_duration

    @property
    def service(self) -> AgentGovernanceService:
        """Return the governance service."""
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        """Initialise the agent governance subsystem.

        Args:
            kernel: The runtime kernel.
        """
        self._log.info("agent_governance.module.start")
        t0 = time.monotonic()

        check = AgentGovernanceHealthCheck(self._service)
        kernel.platform.health.register(check)

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "agent_governance.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Disable all governance policies during shutdown.

        Args:
            _kernel: The runtime kernel.
        """
        self._log.info("agent_governance.module.stop")
        for policy in self._service.list_policies():
            if policy.enabled:
                self._service.update_policy(policy.id, enabled=False)
        self._log.info("agent_governance.module.stopped")


__all__ = ["AgentGovernanceRuntimeModule"]
