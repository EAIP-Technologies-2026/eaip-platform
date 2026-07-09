"""Tests for Agent Runtime domain events."""

from __future__ import annotations

import pytest

from eaip.agents.events import (
    AgentEvent,
    RunCancelled,
    RunCompleted,
    RunFailed,
    RunStarted,
    StepCompleted,
    StepFailed,
    StepStarted,
)
from eaip.events.event import DomainEvent


class TestBaseEvent:
    def test_agent_event_is_domain_event(self) -> None:
        assert issubclass(AgentEvent, DomainEvent)

    def test_event_type_namespace(self) -> None:
        assert AgentEvent.event_type == "eaip.agent.event"


class TestRunStarted:
    def test_fields(self) -> None:
        evt = RunStarted(run_id="r1", agent_id="a1", goal_text="Do something")
        assert evt.run_id == "r1"
        assert evt.agent_id == "a1"
        assert evt.goal_text == "Do something"
        assert evt.event_type == "eaip.agent.run.started"

    def test_frozen(self) -> None:
        evt = RunStarted(run_id="r1", agent_id="a1", goal_text="x")
        with pytest.raises(ValueError):
            evt.run_id = "r2"  # type: ignore[misc]


class TestRunCompleted:
    def test_fields(self) -> None:
        evt = RunCompleted(run_id="r1", agent_id="a1", step_count=3, duration_ms=100.0)
        assert evt.step_count == 3
        assert evt.duration_ms == 100.0
        assert evt.event_type == "eaip.agent.run.completed"


class TestRunFailed:
    def test_fields(self) -> None:
        evt = RunFailed(
            run_id="r1", agent_id="a1", error="something broke", step_count=1, duration_ms=50.0
        )
        assert evt.error == "something broke"
        assert evt.event_type == "eaip.agent.run.failed"


class TestRunCancelled:
    def test_fields(self) -> None:
        evt = RunCancelled(run_id="r1", agent_id="a1", step_count=0)
        assert evt.step_count == 0
        assert evt.event_type == "eaip.agent.run.cancelled"


class TestStepStarted:
    def test_fields(self) -> None:
        evt = StepStarted(run_id="r1", step_id="s1", step_name="echo", step_type="tool_call")
        assert evt.step_name == "echo"
        assert evt.step_type == "tool_call"
        assert evt.event_type == "eaip.agent.step.started"


class TestStepCompleted:
    def test_fields(self) -> None:
        evt = StepCompleted(run_id="r1", step_id="s1", step_name="echo", duration_ms=10.0)
        assert evt.duration_ms == 10.0
        assert evt.event_type == "eaip.agent.step.completed"


class TestStepFailed:
    def test_fields(self) -> None:
        evt = StepFailed(
            run_id="r1", step_id="s1", step_name="echo", error="timeout", duration_ms=30.0
        )
        assert evt.error == "timeout"
        assert evt.event_type == "eaip.agent.step.failed"
