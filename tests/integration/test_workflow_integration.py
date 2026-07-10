"""Integration tests for WorkflowEngine with EventBus, AgentOrchestrator, and StepApprovalHandler."""  # noqa: E501

from __future__ import annotations

import asyncio

from eaip.agents.models import Goal, RunRecord, RunStatus
from eaip.events.bus import EventBus
from eaip.workflow.agents import AgentOrchestrator
from eaip.workflow.approval import StepApprovalHandler
from eaip.workflow.events import (
    WorkflowCompleted,
    WorkflowStarted,
    WorkflowStepCompleted,
    WorkflowStepStarted,
)
from eaip.workflow.executor import WorkflowEngine
from eaip.workflow.models import WorkflowContext, WorkflowDefinition, WorkflowStep


class _TestAgentRuntime:
    _counter = 0

    async def create_run(self, agent_spec: object, goal: Goal) -> RunRecord:
        self._counter += 1
        return RunRecord(
            id=f"run_int_{self._counter}",
            agent_id=agent_spec.id if hasattr(agent_spec, "id") else "unknown",
            goal=goal,
            status=RunStatus.PENDING,
        )

    async def start_run(self, run_id: str) -> RunRecord:
        return RunRecord(
            id=run_id,
            agent_id="agent_mock",
            goal=Goal(text=""),
            status=RunStatus.COMPLETED,
            result=f"result from {run_id}",
        )


class TestWorkflowEngineWithEventBus:
    async def test_events_published_during_execution(self) -> None:
        bus = EventBus()
        events: list = []
        bus.subscribe(WorkflowStarted, events.append)
        bus.subscribe(WorkflowStepStarted, events.append)
        bus.subscribe(WorkflowStepCompleted, events.append)
        bus.subscribe(WorkflowCompleted, events.append)

        engine = WorkflowEngine(agent_runtime=_TestAgentRuntime(), event_bus=bus)
        steps = (
            WorkflowStep(id="s1", name="Step 1", agent_id="agent_a", prompt="Hello"),
            WorkflowStep(id="s2", name="Step 2", agent_id="agent_b", prompt="World"),
        )
        definition = WorkflowDefinition(id="wf_int", name="Integration", steps=steps)
        result = await engine.execute(definition)
        assert result.status == "completed"

        started_events = [e for e in events if isinstance(e, WorkflowStarted)]
        step_started = [e for e in events if isinstance(e, WorkflowStepStarted)]
        step_completed = [e for e in events if isinstance(e, WorkflowStepCompleted)]
        completed_events = [e for e in events if isinstance(e, WorkflowCompleted)]

        assert len(started_events) == 1
        assert len(step_started) == 2
        assert len(step_completed) == 2
        assert len(completed_events) == 1
        assert completed_events[0].workflow_id == "wf_int"


class TestAgentOrchestratorWithEventBus:
    async def test_delegation_publishes_events(self) -> None:
        bus = EventBus()
        events: list = []
        bus.subscribe(WorkflowStarted, events.append)

        orch = AgentOrchestrator(
            agent_runtime=_TestAgentRuntime(),
            event_bus=bus,
        )
        result = await orch.delegate("agent_x", "Do work")
        assert result is not None


class TestStepApprovalHandlerWithEventBus:
    async def test_approval_events_published(self) -> None:
        bus = EventBus()
        approval_events: list = []
        bus.subscribe(WorkflowCompleted, approval_events.append)

        handler = StepApprovalHandler(event_bus=bus)
        token = await handler.request_approval("s1", "run_1", {"step_name": "Review"})
        await handler.approve(token, "run_1")
        status = handler.get_status(token)
        assert status == "approved"


class TestWorkflowEngineWithContext:
    async def test_context_passed_to_steps(self) -> None:
        engine = WorkflowEngine(agent_runtime=_TestAgentRuntime())
        steps = (
            WorkflowStep(id="s1", name="First", agent_id="agent_a", prompt="initial"),
            WorkflowStep(id="s2", name="Second", agent_id="agent_b", prompt="followup"),
        )
        definition = WorkflowDefinition(id="wf_ctx", name="Context", steps=steps)
        ctx = WorkflowContext()
        ctx = ctx.set("env", "test")
        result = await engine.execute(definition, context=ctx)
        assert result.status == "completed"
        assert result.completed_count == 2


class TestWorkflowEngineWithApproval:
    async def test_workflow_with_approval_handler(self) -> None:
        bus = EventBus()
        approval_handler = StepApprovalHandler(event_bus=bus)
        engine = WorkflowEngine(
            agent_runtime=_TestAgentRuntime(),
            event_bus=bus,
            approval_handler=approval_handler,
        )
        steps = (
            WorkflowStep(id="s1", name="Requires Approval", agent_id="agent_a", prompt="needs approval"),  # noqa: E501
        )
        definition = WorkflowDefinition(id="wf_app", name="WithApproval", steps=steps)
        result = await engine.execute(definition)
        assert result.status == "completed"


class TestWorkflowEngineCancellation:
    async def test_cancel_during_execution(self) -> None:
        engine = WorkflowEngine(agent_runtime=_TestAgentRuntime())
        steps = (
            WorkflowStep(id="s1", name="First", agent_id="agent_a", prompt="start"),
        )
        definition = WorkflowDefinition(id="wf_cancel", name="Cancel", steps=steps)
        task = asyncio.create_task(engine.execute(definition))
        await asyncio.sleep(0.01)
        for rid in list(engine._runs):
            await engine.cancel(rid)
        result = await task
        assert result.status in ("cancelled", "completed")
