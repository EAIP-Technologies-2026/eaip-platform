"""Integration layer — AgentPerfRuntimeModule for kernel lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.agentperf.analyzer import AgentPerfAnalyzer
from eaip.agentperf.health import AgentPerfHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AgentPerfRuntimeModule:
    """RuntimeModule that bootstraps the agent performance analyzer subsystem."""

    name: str = "agentperf"

    def __init__(self, analyzer: AgentPerfAnalyzer | None = None) -> None:
        self._analyzer = analyzer or AgentPerfAnalyzer()
        self._log = get_logger("eaip.agentperf.integration")

    @property
    def analyzer(self) -> AgentPerfAnalyzer:
        return self._analyzer

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the agent performance analyzer module."""
        self._log.info("agentperf.module.starting")
        executions = await self._analyzer.list_executions()
        agent_ids = set(e.agent_id for e in executions)
        health_check = AgentPerfHealthCheck(
            execution_count=len(executions),
            agent_count=len(agent_ids),
        )
        kernel.platform.health.register(health_check)
        self._log.info("agentperf.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the agent performance analyzer module."""
        self._log.info("agentperf.module.stopping")


__all__ = ["AgentPerfRuntimeModule"]
