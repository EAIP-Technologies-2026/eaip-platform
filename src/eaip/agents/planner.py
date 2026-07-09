"""Planner implementations — plan generation from goals."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.adapters.llm.models import LLMRequest
from eaip.agents.models import Goal, Plan, Step, StepType
from eaip.providers.models import ChatMessage

if TYPE_CHECKING:
    from eaip.agents.runtime import AgentRunContext


class FixedPlanner:
    """A planner that returns a predefined plan.

    Useful for testing or agents with deterministic execution paths.
    """

    name: str = "fixed"

    def __init__(self, plan: Plan) -> None:  # noqa: D107
        self._plan = plan

    async def create_plan(
        self,
        _goal: Goal,
        _context: AgentRunContext,
    ) -> Plan:
        """Return the predefined plan.

        Args:
            goal: The goal (ignored for this planner).
            context: The agent run context.

        Returns:
            The predefined plan.
        """
        return self._plan


class SimpleLLMPlanner:
    """A planner that uses the LLM to decompose a goal into steps.

    Generates a plan by asking the LLM to break the goal into tool
    calls and LLM completion steps.
    """

    name: str = "simple_llm"

    def __init__(self, max_steps: int = 10) -> None:  # noqa: D107
        self._max_steps = max_steps

    async def create_plan(
        self,
        goal: Goal,
        context: AgentRunContext,
    ) -> Plan:
        """Generate a plan using the configured LLM adapter.

        Args:
            goal: The goal to plan for.
            context: The agent run context.

        Returns:
            A Plan with a sequence of Steps.

        Raises:
            PlanningError: If plan generation fails.
        """
        available_tools = context.tool_registry.all()
        tool_descriptions = "\n".join(f"- {t.name}: {t.description}" for t in available_tools)

        prompt = f"Given the following goal, create a step-by-step plan.\n\nGoal: {goal.text}\n"
        if goal.constraints:
            prompt += f"Constraints: {', '.join(goal.constraints)}\n"
        if tool_descriptions:
            prompt += f"\nAvailable tools:\n{tool_descriptions}\n"
        prompt += (
            f"\nProduce a list of steps, each on a new line, "
            f"formatted as:\n"
            f"  STEP <number>: <type> | <name> | <details>\n"
            f"Where <type> is either 'tool_call' or 'llm_completion'.\n"
            f"For tool_call steps, <details> is the tool name.\n"
            f"For llm_completion steps, <details> is what to ask the LLM.\n"
            f"Maximum {self._max_steps} steps."
        )

        request = LLMRequest(
            model="default",
            messages=(ChatMessage(role="user", content=prompt),),
            metadata={"purpose": "planning"},
        )
        llm_context = context.to_run_context()
        response = await context.llm_adapter.complete(request, context=llm_context)

        steps = self._parse_steps(response.content, goal)
        return Plan(goal=goal, steps=steps, reasoning=response.content)

    def _parse_steps(self, content: str, goal: Goal) -> tuple[Step, ...]:
        """Parse steps from the LLM response text."""
        steps: list[Step] = []
        for raw_line in content.strip().split("\n"):
            line = raw_line.strip()
            if not line.startswith("STEP "):
                continue

            try:
                rest = line[len("STEP ") :]
                num_str, rest = rest.split(":", 1)
                step_num = int(num_str.strip())
                type_str, rest = rest.split("|", 1)
                step_type_str = type_str.strip()
                name_str, detail_str = rest.split("|", 1)
                name = name_str.strip()
                detail = detail_str.strip()
            except (ValueError, IndexError):
                continue

            if step_type_str == "tool_call":
                steps.append(
                    Step(
                        id=f"step_{step_num}",
                        name=name or detail,
                        type=StepType.TOOL_CALL,
                        tool_name=detail,
                    )
                )
            elif step_type_str == "llm_completion":
                steps.append(
                    Step(
                        id=f"step_{step_num}",
                        name=name or detail,
                        type=StepType.LLM_COMPLETION,
                        prompt=detail,
                    )
                )

        if not steps:
            steps.append(
                Step(
                    id="step_1",
                    name="llm_respond",
                    type=StepType.LLM_COMPLETION,
                    prompt=goal.text,
                )
            )

        return tuple(steps)


__all__ = ["FixedPlanner", "SimpleLLMPlanner"]
