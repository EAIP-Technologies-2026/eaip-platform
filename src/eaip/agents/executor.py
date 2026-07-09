"""Step executor — executes individual agent steps."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.adapters.llm.models import LLMRequest
from eaip.agents.exceptions import StepExecutionError
from eaip.agents.models import Step, StepStatus, StepType
from eaip.providers.models import ChatMessage

if TYPE_CHECKING:
    from eaip.agents.models import RunRecord
    from eaip.agents.runtime import AgentRunContext


class StepExecutor:
    """Executes individual agent steps.

    Supports ``TOOL_CALL`` and ``LLM_COMPLETION`` step types.
    """

    async def execute(
        self,
        step: Step,
        _run: RunRecord,
        context: AgentRunContext,
    ) -> Step:
        """Execute a single step and return the updated step.

        Args:
            step: The step to execute.
            _run: The parent run record (unused).
            context: The agent run context.

        Returns:
            The completed step with output, status, and duration populated.
        """
        if step.status is not StepStatus.PENDING:
            return step

        start = time.monotonic()
        try:
            result = await self._dispatch(step, context)
            elapsed = time.monotonic() - start
            return Step(
                id=step.id,
                name=step.name,
                type=step.type,
                tool_name=step.tool_name,
                prompt=step.prompt,
                input=step.input,
                output=result,
                status=StepStatus.COMPLETED,
                error=None,
                duration_ms=elapsed * 1000,
            )
        except Exception as exc:
            elapsed = time.monotonic() - start
            return Step(
                id=step.id,
                name=step.name,
                type=step.type,
                tool_name=step.tool_name,
                prompt=step.prompt,
                input=step.input,
                output="",
                status=StepStatus.FAILED,
                error=str(exc),
                duration_ms=elapsed * 1000,
            )

    async def _dispatch(self, step: Step, context: AgentRunContext) -> str:
        """Dispatch step execution based on type."""
        _handlers = {
            StepType.TOOL_CALL: self._execute_tool,
            StepType.LLM_COMPLETION: self._execute_llm,
        }
        handler = _handlers.get(step.type)
        if handler is not None:
            return await handler(step, context)
        raise StepExecutionError(step.name, f"unknown step type: {step.type}")

    async def _execute_tool(
        self,
        step: Step,
        context: AgentRunContext,
    ) -> str:
        """Execute a tool call step."""
        tool = context.tool_registry.try_get(step.tool_name)
        if tool is None:
            raise StepExecutionError(
                step.name,
                f"tool not found: {step.tool_name!r}",
            )
        return await tool.execute(**step.input)

    async def _execute_llm(
        self,
        step: Step,
        context: AgentRunContext,
    ) -> str:
        """Execute an LLM completion step."""
        request = LLMRequest(
            model=step.tool_name or "default",
            messages=(ChatMessage(role="user", content=step.prompt),),
            metadata={"step_id": step.id, "step_name": step.name},
        )
        llm_context = context.to_run_context()
        response = await context.llm_adapter.complete(request, context=llm_context)
        return response.content


__all__ = ["StepExecutor"]
