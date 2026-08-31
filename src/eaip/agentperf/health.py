"""Health check for the agent performance analyzer."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class AgentPerfHealthCheck:
    """Health check for the agent performance analyzer."""

    name: str = "agentperf"

    def __init__(self, execution_count: int = 0, agent_count: int = 0) -> None:
        self._execution_count = execution_count
        self._agent_count = agent_count

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        details = {
            "execution_count": self._execution_count,
            "agent_count": self._agent_count,
        }
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message=f"{self._agent_count} agent(s), {self._execution_count} execution(s)",
            details=details,
        )


__all__ = ["AgentPerfHealthCheck"]
