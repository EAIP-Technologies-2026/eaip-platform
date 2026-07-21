"""Agent template runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.agenttpl.health import AgentTemplateHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AgentTemplateRuntimeModule:
    """Runtime module for agent templates."""

    name: str = "agenttpl"

    def __init__(self) -> None:
        """Initialize the agent template runtime module."""
        self._health_check = AgentTemplateHealthCheck()
        self._log = get_logger("eaip.agenttpl.integration")

    @property
    def health_check(self) -> AgentTemplateHealthCheck:
        """Return the agent template health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("agenttpl.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("agenttpl.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("agenttpl.module.stopping")


__all__ = ["AgentTemplateRuntimeModule"]
