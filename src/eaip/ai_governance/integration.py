"""Integration layer — AiGovernanceRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.ai_governance.health import AiGovernanceHealthCheck
from eaip.ai_governance.service import AiGovernanceService
from eaip.health.checks import HealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AiGovernanceRuntimeModule:
    """RuntimeModule that bootstraps the AI Governance subsystem during kernel start."""

    name: str = "ai_governance"

    def __init__(self, service: AiGovernanceService | None = None) -> None:
        """Initialize the AI Governance runtime module.

        Args:
            service: Optional AiGovernanceService instance.
        """
        self._service = service or AiGovernanceService()
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.ai_governance.integration")

    @property
    def service(self) -> AiGovernanceService:
        """Return the AI Governance service."""
        return self._service

    @property
    def startup_duration(self) -> float:
        """Return the startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the AI Governance module.

        Args:
            kernel: Optional runtime kernel for health check registration.
        """
        t0 = time.monotonic()
        self._log.info("ai_governance.integration.start")

        if kernel is not None:
            check = await self._health_check()
            kernel.platform.health.register(check)

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info(
            "ai_governance.integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the AI Governance module.

        Args:
            _kernel: Optional runtime kernel (unused).
        """
        self._log.info("ai_governance.integration.stop")
        self._started = False

    async def _health_check(self) -> HealthCheck:
        policies = await self._service.list_policies()
        requirements = await self._service.list_requirements()
        return AiGovernanceHealthCheck(
            policy_count=len(policies),
            requirement_count=len(requirements),
        )


__all__ = ["AiGovernanceRuntimeModule"]
