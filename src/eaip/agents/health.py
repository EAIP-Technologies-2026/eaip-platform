"""Agent runtime health check."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.health.checks import HealthReport

if TYPE_CHECKING:
    from eaip.agents.runtime import AgentRuntime


class AgentHealthCheck:
    """Health check for the agent runtime subsystem.

    Reports the number of active runs and overall subsystem health.
    """

    name: str = "agent_runtime"

    def __init__(self, runtime: AgentRuntime) -> None:  # noqa: D107
        self._runtime = runtime

    async def check(self) -> HealthReport:
        """Check the health of the agent runtime.

        Returns:
            A HealthReport.
        """
        return await self._runtime.health()


__all__ = ["AgentHealthCheck"]
