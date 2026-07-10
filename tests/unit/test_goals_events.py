"""Tests for goal domain events."""

from __future__ import annotations

import pytest

from eaip.events.event import DomainEvent
from eaip.goals.events import (
    GoalCompleted,
    GoalCreated,
    GoalFailed,
    GoalProgressUpdated,
    GoalUpdated,
    KpiThresholdMet,
    KpiUpdated,
    ObjectiveAssigned,
)


class TestGoalCreated:
    def test_defaults(self) -> None:
        e = GoalCreated()
        assert e.event_type == "eaip.goals.goal.created"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = GoalCreated(goal_id="g1", goal_name="Test", owner="owner@co.com", priority="high")
        assert e.goal_id == "g1"
        assert e.goal_name == "Test"
        assert e.owner == "owner@co.com"
        assert e.priority == "high"

    def test_frozen(self) -> None:
        e = GoalCreated(goal_id="g1")
        with pytest.raises((ValueError, TypeError)):
            e.goal_id = "g2"


class TestGoalUpdated:
    def test_defaults(self) -> None:
        e = GoalUpdated()
        assert e.event_type == "eaip.goals.goal.updated"
        assert e.changes == {}

    def test_with_changes(self) -> None:
        e = GoalUpdated(goal_id="g1", changes={"status": "active"})
        assert e.changes == {"status": "active"}


class TestGoalCompleted:
    def test_defaults(self) -> None:
        e = GoalCompleted()
        assert e.event_type == "eaip.goals.goal.completed"
        assert e.final_progress == 0.0

    def test_with_values(self) -> None:
        e = GoalCompleted(goal_id="g1", goal_name="Test", final_progress=100.0)
        assert e.final_progress == 100.0


class TestGoalFailed:
    def test_defaults(self) -> None:
        e = GoalFailed()
        assert e.event_type == "eaip.goals.goal.failed"
        assert e.reason == ""

    def test_with_reason(self) -> None:
        e = GoalFailed(goal_id="g1", goal_name="Test", reason="budget exceeded")
        assert e.reason == "budget exceeded"


class TestGoalProgressUpdated:
    def test_defaults(self) -> None:
        e = GoalProgressUpdated()
        assert e.event_type == "eaip.goals.goal.progress_updated"

    def test_with_values(self) -> None:
        e = GoalProgressUpdated(
            goal_id="g1",
            overall_progress=75.0,
            objectives_progress={"o1": 80.0},
            kpi_values={"k1": 0.9},
        )
        assert e.overall_progress == 75.0
        assert e.objectives_progress == {"o1": 80.0}
        assert e.kpi_values == {"k1": 0.9}


class TestObjectiveAssigned:
    def test_defaults(self) -> None:
        e = ObjectiveAssigned()
        assert e.event_type == "eaip.goals.objective.assigned"

    def test_with_values(self) -> None:
        e = ObjectiveAssigned(objective_id="o1", goal_id="g1", worker_id="w1")
        assert e.objective_id == "o1"
        assert e.worker_id == "w1"


class TestKpiUpdated:
    def test_defaults(self) -> None:
        e = KpiUpdated()
        assert e.event_type == "eaip.goals.kpi.updated"

    def test_with_values(self) -> None:
        e = KpiUpdated(kpi_id="k1", goal_id="g1", previous_value=10.0, new_value=25.0)
        assert e.previous_value == 10.0
        assert e.new_value == 25.0


class TestKpiThresholdMet:
    def test_defaults(self) -> None:
        e = KpiThresholdMet()
        assert e.event_type == "eaip.goals.kpi.threshold_met"

    def test_with_values(self) -> None:
        e = KpiThresholdMet(
            kpi_id="k1",
            goal_id="g1",
            kpi_name="Revenue",
            current_value=1_000_000.0,
            threshold=0.95,
        )
        assert e.kpi_name == "Revenue"
        assert e.current_value == 1_000_000.0
        assert e.threshold == 0.95
