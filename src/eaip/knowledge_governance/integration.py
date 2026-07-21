"""Integration layer — KnowledgeGovernanceRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.health.checks import HealthCheck
from eaip.knowledge_governance.health import KnowledgeGovernanceHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class KnowledgeGovernanceRuntimeModule:
    """RuntimeModule that bootstraps the Knowledge Governance subsystem during kernel start."""

    name: str = "knowledge_governance"

    def __init__(self) -> None:
        """Initialize the knowledge governance runtime module."""
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.knowledge_governance.integration")

    @property
    def startup_duration(self) -> float:
        """Return the startup duration."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the knowledge governance module.

        Args:
            kernel: Optional runtime kernel for platform integration.
        """
        t0 = time.monotonic()
        self._log.info("kg.integration.start")

        if kernel is not None:
            kernel.platform.health.register(self._health_check())

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info(
            "kg.integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the knowledge governance module."""
        self._log.info("kg.integration.stop")
        self._started = False

    def _health_check(self) -> HealthCheck:
        return KnowledgeGovernanceHealthCheck()


__all__ = ["KnowledgeGovernanceRuntimeModule"]
