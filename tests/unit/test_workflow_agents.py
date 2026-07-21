"""Tests for AgentOrchestrator - delegation, handoff, messaging, shared context."""

from __future__ import annotations

import pytest

from eaip.agents.models import Goal, RunRecord, RunStatus
from eaip.workflow.agents import AgentOrchestrator
from eaip.workflow.exceptions import AgentDelegationError
from eaip.workflow.models import WorkflowContext


class _MockAgentRuntime:
    def __init__(self) -> None:
        self.runs: dict[str, RunRecord] = {}
        self._counter = 0

    async def create_run(self, agent_spec: object, goal: Goal) -> RunRecord:
        self._counter += 1
        run_id = f"run_{self._counter}"
        run = RunRecord(
            id=run_id,
            agent_id=agent_spec.id if hasattr(agent_spec, "id") else "unknown",
            goal=goal,
            status=RunStatus.PENDING,
        )
        self.runs[run_id] = run
        return run

    async def start_run(self, run_id: str) -> RunRecord:
        run = self.runs.get(run_id)
        if run is None:
            return RunRecord(
                id=run_id,
                agent_id="unknown",
                goal=Goal(text=""),
                status=RunStatus.FAILED,
                error="not found",
            )
        completed = RunRecord(
            id=run.id,
            agent_id=run.agent_id,
            goal=run.goal,
            status=RunStatus.COMPLETED,
            result=f"output for {run.agent_id}: {run.goal.text}",
        )
        self.runs[run_id] = completed
        return completed


class _FailingMockAgentRuntime:
    async def create_run(self, agent_spec: object, goal: Goal) -> RunRecord:
        return RunRecord(
            id="run_fail",
            agent_id=agent_spec.id if hasattr(agent_spec, "id") else "unknown",
            goal=goal,
            status=RunStatus.FAILED,
            error="intentional failure",
        )

    async def start_run(self, run_id: str) -> RunRecord:
        return RunRecord(
            id=run_id,
            agent_id="unknown",
            goal=Goal(text=""),
            status=RunStatus.FAILED,
            error="intentional failure",
        )


@pytest.fixture
def runtime() -> _MockAgentRuntime:
    return _MockAgentRuntime()


@pytest.fixture
def orchestrator(runtime: _MockAgentRuntime) -> AgentOrchestrator:
    return AgentOrchestrator(agent_runtime=runtime)


class TestAgentOrchestratorDelegation:
    async def test_delegate_success(self, orchestrator: AgentOrchestrator) -> None:
        output = await orchestrator.delegate("agent_a", "Do something important")
        assert "agent_a" in output
        assert "Do something important" in output

    async def test_delegate_with_context(self, orchestrator: AgentOrchestrator) -> None:
        ctx = WorkflowContext()
        ctx = ctx.set("env", "prod")
        output = await orchestrator.delegate("agent_b", "Process order", _workflow_context=ctx)
        assert "agent_b" in output

    async def test_delegate_failure(self) -> None:
        orch = AgentOrchestrator(agent_runtime=_FailingMockAgentRuntime())
        with pytest.raises(AgentDelegationError):
            await orch.delegate("agent_x", "will fail")

    async def test_delegate_async(self, orchestrator: AgentOrchestrator) -> None:
        run_id = await orchestrator.delegate_async("agent_c", "Background task")
        assert run_id.startswith("run_")

    async def test_wait_for_agent_success(
        self,
        orchestrator: AgentOrchestrator,
        runtime: _MockAgentRuntime,
    ) -> None:
        run_id = await orchestrator.delegate_async("agent_d", "Delayed task")
        output = await orchestrator.wait_for_agent(run_id)
        assert "agent_d" in output

    async def test_wait_for_agent_failure(self) -> None:
        orch = AgentOrchestrator(agent_runtime=_FailingMockAgentRuntime())
        with pytest.raises(AgentDelegationError):
            await orch.wait_for_agent("run_fail")


class TestAgentOrchestratorHandoff:
    async def test_handoff_basic(self, orchestrator: AgentOrchestrator) -> None:
        output = await orchestrator.handoff("agent_a", "agent_b", "Continue the work")
        assert "agent_b" in output

    async def test_handoff_tracking(self, orchestrator: AgentOrchestrator) -> None:
        await orchestrator.handoff("agent_a", "agent_b", "Task 1")
        await orchestrator.handoff("agent_a", "agent_c", "Task 2")
        handoffs = orchestrator.get_handoffs("agent_a")
        assert len(handoffs) == 2
        assert handoffs[0]["to_agent_id"] == "agent_b"
        assert handoffs[1]["to_agent_id"] == "agent_c"

    async def test_handoff_empty(self, orchestrator: AgentOrchestrator) -> None:
        assert orchestrator.get_handoffs("unknown") == []


class TestAgentOrchestratorMessaging:
    async def test_send_and_read_messages(self) -> None:
        orch = AgentOrchestrator(agent_runtime=_MockAgentRuntime())
        await orch.send_message("agent_a", {"type": "info", "content": "hello"})
        msgs = await orch.read_messages("agent_a")
        assert len(msgs) == 1
        assert msgs[0]["message"]["content"] == "hello"

    async def test_read_empty_inbox(self) -> None:
        orch = AgentOrchestrator(agent_runtime=_MockAgentRuntime())
        msgs = await orch.read_messages("agent_z")
        assert msgs == []

    async def test_messages_mark_as_read(self) -> None:
        orch = AgentOrchestrator(agent_runtime=_MockAgentRuntime())
        await orch.send_message("agent_x", {"msg": "test"})
        msgs = await orch.read_messages("agent_x")
        assert msgs[0]["read"] is True

    async def test_delegate_without_context(self, orchestrator: AgentOrchestrator) -> None:
        output = await orchestrator.delegate("agent_n", "No context")
        assert output is not None
