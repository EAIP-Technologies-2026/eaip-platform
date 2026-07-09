"""Agent Runtime exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError


class AgentError(EAIPError):
    """Base for agent-related failures."""


class AgentNotFoundError(AgentError):
    """Raised when a requested agent spec is not found."""

    def __init__(self, agent_id: str) -> None:  # noqa: D107
        self.agent_id = agent_id
        super().__init__(f"agent not found: {agent_id!r}")


class RunNotFoundError(AgentError):
    """Raised when a requested run is not found."""

    def __init__(self, run_id: str) -> None:  # noqa: D107
        self.run_id = run_id
        super().__init__(f"run not found: {run_id!r}")


class PlanningError(AgentError):
    """Raised when plan generation fails."""


class StepExecutionError(AgentError):
    """Raised when a step fails during execution."""

    def __init__(self, step_name: str, message: str) -> None:  # noqa: D107
        self.step_name = step_name
        super().__init__(f"step {step_name!r} failed: {message}")


__all__ = [
    "AgentError",
    "AgentNotFoundError",
    "PlanningError",
    "RunNotFoundError",
    "StepExecutionError",
]
