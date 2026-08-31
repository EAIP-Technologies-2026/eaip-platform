"""Tests for goal models."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.goals.models import (
    BusinessGoal,
    GoalConfig,
    GoalProgress,
    GoalStatus,
    KpiDefinition,
    KpiDirection,
    MeasurementType,
    Objective,
    ObjectiveStatus,
    Priority,
)
from eaip.shared.time import utc_now


class TestGoalStatus:
    def test_values(self) -> None:
        assert GoalStatus.DRAFT == "draft"
        assert GoalStatus.ACTIVE == "active"
        assert GoalStatus.COMPLETED == "completed"
        assert GoalStatus.FAILED == "failed"
        assert GoalStatus.CANCELLED == "cancelled"

    def test_valid_members(self) -> None:
        assert len(GoalStatus) == 5


class TestPriority:
    def test_values(self) -> None:
        assert Priority.LOW == "low"
        assert Priority.MEDIUM == "medium"
        assert Priority.HIGH == "high"
        assert Priority.CRITICAL == "critical"

    def test_valid_members(self) -> None:
        assert len(Priority) == 4


class TestMeasurementType:
    def test_values(self) -> None:
        assert MeasurementType.COUNT == "count"
        assert MeasurementType.DURATION == "duration"
        assert MeasurementType.PERCENTAGE == "percentage"
        assert MeasurementType.BINARY == "binary"


class TestKpiDirection:
    def test_values(self) -> None:
        assert KpiDirection.HIGHER_IS_BETTER == "higher_is_better"
        assert KpiDirection.LOWER_IS_BETTER == "lower_is_better"


class TestObjectiveStatus:
    def test_values(self) -> None:
        assert ObjectiveStatus.PENDING == "pending"
        assert ObjectiveStatus.IN_PROGRESS == "in_progress"
        assert ObjectiveStatus.COMPLETED == "completed"
        assert ObjectiveStatus.FAILED == "failed"
        assert ObjectiveStatus.BLOCKED == "blocked"


class TestKpiDefinition:
    def test_defaults(self) -> None:
        k = KpiDefinition(id="k1", name="Test KPI")
        assert k.id == "k1"
        assert k.name == "Test KPI"
        assert k.description == ""
        assert k.unit == ""
        assert k.target_value == 0.0
        assert k.current_value == 0.0
        assert k.measurement_type is MeasurementType.COUNT
        assert k.direction is KpiDirection.HIGHER_IS_BETTER
        assert k.met_threshold == 1.0

    def test_custom(self) -> None:
        k = KpiDefinition(
            id="k2",
            name="CPU Usage",
            description="Average CPU utilization",
            unit="%",
            target_value=80.0,
            current_value=45.0,
            measurement_type=MeasurementType.PERCENTAGE,
            direction=KpiDirection.LOWER_IS_BETTER,
            met_threshold=0.95,
        )
        assert k.unit == "%"
        assert k.target_value == 80.0
        assert k.current_value == 45.0
        assert k.measurement_type is MeasurementType.PERCENTAGE
        assert k.direction is KpiDirection.LOWER_IS_BETTER
        assert k.met_threshold == 0.95

    def test_frozen(self) -> None:
        k = KpiDefinition(id="k1", name="Test")
        with pytest.raises(ValueError):
            k.name = "Changed"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValueError):
            KpiDefinition(id="k1", name="Test", extra_field="x")  # type: ignore[call-arg]


class TestObjective:
    def test_defaults(self) -> None:
        o = Objective(id="o1", goal_id="g1", name="Test Objective")
        assert o.id == "o1"
        assert o.goal_id == "g1"
        assert o.status is ObjectiveStatus.PENDING
        assert o.weight == 1.0
        assert o.kpis == ()
        assert o.target_value == 0.0
        assert o.current_value == 0.0
        assert o.assigned_worker_id == ""
        assert o.deadline is None

    def test_with_kpis(self) -> None:
        kpi = KpiDefinition(id="k1", name="KPI 1", target_value=100.0)
        o = Objective(
            id="o2",
            goal_id="g1",
            name="With KPIs",
            weight=0.5,
            kpis=(kpi,),
            target_value=100.0,
            current_value=50.0,
            assigned_worker_id="w1",
            deadline=utc_now(),
        )
        assert o.weight == 0.5
        assert len(o.kpis) == 1
        assert o.kpis[0].id == "k1"
        assert o.target_value == 100.0
        assert o.current_value == 50.0
        assert o.assigned_worker_id == "w1"

    def test_weight_validation(self) -> None:
        with pytest.raises(ValueError):
            Objective(id="o1", goal_id="g1", name="Bad", weight=1.5)
        with pytest.raises(ValueError):
            Objective(id="o1", goal_id="g1", name="Bad", weight=-0.1)

    def test_frozen(self) -> None:
        o = Objective(id="o1", goal_id="g1", name="Test")
        with pytest.raises(ValueError):
            o.name = "Changed"  # type: ignore[misc]


class TestBusinessGoal:
    def test_defaults(self) -> None:
        g = BusinessGoal(id="g1", name="Test Goal")
        assert g.id == "g1"
        assert g.name == "Test Goal"
        assert g.description == ""
        assert g.status is GoalStatus.DRAFT
        assert g.priority is Priority.MEDIUM
        assert g.owner == ""
        assert g.kpis == ()
        assert g.objectives == ()
        assert g.deadline is None
        assert g.tags == ()
        assert g.metadata == {}

    def test_with_all_fields(self) -> None:
        now = utc_now()
        kpi = KpiDefinition(id="k1", name="Revenue", target_value=1_000_000.0)
        obj = Objective(id="o1", goal_id="g1", name="Increase Revenue", kpis=(kpi,))
        g = BusinessGoal(
            id="g1",
            name="Q4 Growth",
            description="Achieve Q4 revenue targets",
            status=GoalStatus.ACTIVE,
            priority=Priority.HIGH,
            owner="owner@co.com",
            kpis=(kpi,),
            objectives=(obj,),
            deadline=now,
            tags=("quarterly", "revenue"),
            metadata={"department": "sales"},
        )
        assert g.status is GoalStatus.ACTIVE
        assert g.priority is Priority.HIGH
        assert g.owner == "owner@co.com"
        assert len(g.kpis) == 1
        assert len(g.objectives) == 1
        assert g.deadline == now
        assert g.tags == ("quarterly", "revenue")
        assert g.metadata == {"department": "sales"}

    def test_frozen(self) -> None:
        g = BusinessGoal(id="g1", name="Test")
        with pytest.raises(ValueError):
            g.name = "Changed"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValueError):
            BusinessGoal(id="g1", name="Test", extra="x")  # type: ignore[call-arg]


class TestGoalProgress:
    def test_defaults(self) -> None:
        p = GoalProgress(goal_id="g1")
        assert p.goal_id == "g1"
        assert p.overall_progress == 0.0
        assert p.objectives_progress == {}
        assert p.kpi_values == {}
        assert isinstance(p.last_updated, datetime)

    def test_custom_progress(self) -> None:
        p = GoalProgress(
            goal_id="g1",
            overall_progress=75.5,
            objectives_progress={"o1": 80.0, "o2": 70.0},
            kpi_values={"k1": 0.9},
        )
        assert p.overall_progress == 75.5
        assert p.objectives_progress == {"o1": 80.0, "o2": 70.0}
        assert p.kpi_values == {"k1": 0.9}

    def test_mutable(self) -> None:
        p = GoalProgress(goal_id="g1")
        p.overall_progress = 50.0
        assert p.overall_progress == 50.0

    def test_progress_validation(self) -> None:
        with pytest.raises(ValueError):
            GoalProgress(goal_id="g1", overall_progress=150.0)
        with pytest.raises(ValueError):
            GoalProgress(goal_id="g1", overall_progress=-10.0)


class TestGoalConfig:
    def test_defaults(self) -> None:
        c = GoalConfig()
        assert c.evaluation_interval_seconds == 60.0
        assert c.enable_auto_replan is False
        assert c.max_objectives == 20
        assert c.notification_thresholds == {"warning": 0.7, "critical": 0.9}

    def test_custom(self) -> None:
        c = GoalConfig(
            evaluation_interval_seconds=120.0,
            enable_auto_replan=True,
            max_objectives=50,
            notification_thresholds={"warning": 0.8},
        )
        assert c.evaluation_interval_seconds == 120.0
        assert c.enable_auto_replan is True
        assert c.max_objectives == 50
        assert c.notification_thresholds == {"warning": 0.8}

    def test_frozen(self) -> None:
        c = GoalConfig()
        with pytest.raises(ValueError):
            c.max_objectives = 30  # type: ignore[misc]
