"""Tests for :mod:`eaip.agentperf.events`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.agentperf.events import (
    AgentComparisonCompleted,
    BottleneckDetected,
    ExecutionRecorded,
)

ExecutionRecorded.__test__ = False
BottleneckDetected.__test__ = False
AgentComparisonCompleted.__test__ = False


class TestAgentPerfEvents:
    def test_execution_recorded(self) -> None:
        e = ExecutionRecorded(
            execution_id="e1",
            agent_id="a1",
            task_type="reasoning",
            duration_ms=1500.0,
            success=True,
        )
        assert e.event_type == "eaip.agentperf.execution.recorded"
        assert e.execution_id == "e1"
        assert e.agent_id == "a1"
        assert e.duration_ms == 1500.0

    def test_bottleneck_detected(self) -> None:
        e = BottleneckDetected(
            report_id="r1",
            agent_id="a1",
            metric="duration",
            actual_value=10000.0,
            threshold=5000.0,
        )
        assert e.event_type == "eaip.agentperf.bottleneck.detected"
        assert e.metric == "duration"
        assert e.actual_value == 10000.0

    def test_agent_comparison_completed(self) -> None:
        e = AgentComparisonCompleted(
            comparison_id="c1",
            agent_ids=("a1", "a2"),
            metric="duration_ms",
        )
        assert e.event_type == "eaip.agentperf.comparison.completed"
        assert "a1" in e.agent_ids


class TestEventImmutability:
    def test_execution_recorded_frozen(self) -> None:
        e = ExecutionRecorded(
            execution_id="e1", agent_id="a1", task_type="t", duration_ms=1.0, success=True
        )
        with pytest.raises(ValidationError):
            e.agent_id = "changed"


class TestEventOccurredAt:
    def test_has_timestamp(self) -> None:
        e = ExecutionRecorded(
            execution_id="e1", agent_id="a1", task_type="t", duration_ms=1.0, success=True
        )
        assert e.occurred_at is not None
