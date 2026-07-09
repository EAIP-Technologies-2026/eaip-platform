"""Agent Runtime protocols — Agent, Planner, Guardrail."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from eaip.agents.models import Goal, Plan, RunRecord, Step

if TYPE_CHECKING:
    from eaip.agents.runtime import AgentRunContext


@runtime_checkable
class Agent(Protocol):
    """Protocol for executable agent implementations.

    Implementations must provide:
    - ``name`` — unique agent name.
    - ``description`` — human-readable description.
    - ``create_run()`` — creates a RunRecord for the given goal.
    - ``execute_run()`` — executes the run to completion.
    """

    name: str
    description: str

    async def create_run(self, goal: Goal) -> RunRecord:
        """Create a new run for the given goal.

        Args:
            goal: The goal to accomplish.

        Returns:
            A pending RunRecord.
        """
        ...

    async def execute_run(self, run: RunRecord) -> RunRecord:
        """Execute a run to completion.

        Args:
            run: The run to execute (must be in PENDING status).

        Returns:
            The completed RunRecord.
        """
        ...


@runtime_checkable
class Planner(Protocol):
    """Protocol for plan generation.

    Implementations must provide:
    - ``name`` — unique planner name.
    - ``create_plan()`` — produce a Plan from a Goal.
    """

    name: str

    async def create_plan(
        self,
        goal: Goal,
        context: AgentRunContext,
    ) -> Plan:
        """Produce a plan for achieving a goal.

        Args:
            goal: The goal to plan for.
            context: The agent run context.

        Returns:
            A Plan with a sequence of Steps.
        """
        ...


class GuardrailResult(BaseModel):
    """Result of a guardrail check before or after a step."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    blocked: bool = False
    reason: str = ""
    modified_step: Step | None = None


@runtime_checkable
class Guardrail(Protocol):
    """Protocol for pre/post step guardrails.

    Implementations must provide:
    - ``name`` — unique guardrail name.
    - ``before_step()`` — inspect/modify/block a step before execution.
    - ``after_step()`` — inspect/review a step after execution.
    """

    name: str

    async def before_step(
        self,
        step: Step,
        context: AgentRunContext,
    ) -> GuardrailResult:
        """Inspect or modify a step before execution.

        Args:
            step: The step about to be executed.
            context: The agent run context.

        Returns:
            A GuardrailResult indicating whether the step is blocked or modified.
        """
        ...

    async def after_step(
        self,
        step: Step,
        context: AgentRunContext,
    ) -> GuardrailResult:
        """Inspect or review a step after execution.

        Args:
            step: The step that was executed.
            context: The agent run context.

        Returns:
            A GuardrailResult (blocked steps can halt the run).
        """
        ...


__all__ = [
    "Agent",
    "Guardrail",
    "GuardrailResult",
    "Planner",
]
