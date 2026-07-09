"""Tests for the StepExecutor."""

from __future__ import annotations

import pytest

from eaip.adapters.llm.models import LLMRequest, LLMResponse, RunContext as LLMRunContext
from eaip.agents.executor import StepExecutor
from eaip.agents.models import Goal, RunRecord, Step, StepStatus, StepType
from eaip.agents.runtime import AgentRunContext
from eaip.health.checks import HealthReport, HealthStatus
from eaip.tools.registry import ToolRegistry


class _MockLLMAdapter:
    name = "mock"
    version = "0.1.0"

    async def complete(
        self, request: LLMRequest, *, context: LLMRunContext | None = None
    ) -> LLMResponse:
        return LLMResponse(
            model="mock",
            provider="mock",
            content=f"Response to: {request.messages[0].content[:50]}",
            finish_reason="stop",
        )

    async def health(self) -> object:
        return HealthReport(component="mock", status=HealthStatus.HEALTHY)


class _EchoTool:
    name = "echo"
    description = "Echo back"

    @property
    def parameters(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        }

    async def execute(self, **kwargs: object) -> str:
        return f"echo: {kwargs.get('message', '')}"


class _FailingTool:
    name = "fail"
    description = "Always fails"

    @property
    def parameters(self) -> dict[str, object]:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs: object) -> str:
        raise RuntimeError("tool error")


@pytest.fixture
def tool_registry() -> ToolRegistry:
    r = ToolRegistry()
    r.register(_EchoTool())
    r.register(_FailingTool())
    return r


@pytest.fixture
def context(tool_registry: ToolRegistry) -> AgentRunContext:
    return AgentRunContext(
        llm_adapter=_MockLLMAdapter(),
        tool_registry=tool_registry,
    )


@pytest.fixture
def executor() -> StepExecutor:
    return StepExecutor()


@pytest.fixture
def run_record() -> RunRecord:
    return RunRecord(id="run_1", agent_id="agent_1", goal=Goal(text="test"))


class TestStepExecutor:
    async def test_execute_tool_call_success(
        self,
        executor: StepExecutor,
        context: AgentRunContext,
        run_record: RunRecord,
    ) -> None:
        step = Step(
            id="s1",
            name="echo_hello",
            type=StepType.TOOL_CALL,
            tool_name="echo",
            input={"message": "hello"},
        )
        result = await executor.execute(step, run_record, context)
        assert result.status is StepStatus.COMPLETED
        assert "echo" in result.output.lower()
        assert result.error is None
        assert result.duration_ms > 0

    async def test_execute_llm_completion_success(
        self,
        executor: StepExecutor,
        context: AgentRunContext,
        run_record: RunRecord,
    ) -> None:
        step = Step(
            id="s1",
            name="ask_llm",
            type=StepType.LLM_COMPLETION,
            prompt="What is the meaning of life?",
        )
        result = await executor.execute(step, run_record, context)
        assert result.status is StepStatus.COMPLETED
        assert "Response to" in result.output
        assert result.error is None

    async def test_execute_tool_not_found(
        self,
        executor: StepExecutor,
        context: AgentRunContext,
        run_record: RunRecord,
    ) -> None:
        step = Step(
            id="s1",
            name="unknown_tool",
            type=StepType.TOOL_CALL,
            tool_name="nonexistent_tool",
        )
        result = await executor.execute(step, run_record, context)
        assert result.status is StepStatus.FAILED
        assert "not found" in (result.error or "")

    async def test_execute_tool_failure(
        self,
        executor: StepExecutor,
        context: AgentRunContext,
        run_record: RunRecord,
    ) -> None:
        step = Step(
            id="s1",
            name="fail_tool",
            type=StepType.TOOL_CALL,
            tool_name="fail",
        )
        result = await executor.execute(step, run_record, context)
        assert result.status is StepStatus.FAILED
        assert result.error is not None

    async def test_skip_non_pending_step(
        self,
        executor: StepExecutor,
        context: AgentRunContext,
        run_record: RunRecord,
    ) -> None:
        step = Step(
            id="s1",
            name="already_done",
            type=StepType.TOOL_CALL,
            status=StepStatus.COMPLETED,
            output="already done",
        )
        result = await executor.execute(step, run_record, context)
        assert result.output == "already done"
        assert result.status is StepStatus.COMPLETED
