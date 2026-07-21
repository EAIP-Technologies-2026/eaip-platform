"""Tests for DR domain events."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.dr.events import (
    DrPlanActivated,
    DrPlanCreated,
    DrPlanTested,
    DrPlanTestFailed,
    FailoverCompleted,
    FailoverFailed,
    FailoverRolledBack,
    FailoverStarted,
    RtoRpoViolation,
)
from eaip.dr.models import (
    DrPlan,
    DrTestResult,
    FailoverEvent,
)
from eaip.events.event import DomainEvent


class TestDrEvents:
    def test_dr_plan_created(self) -> None:
        plan = DrPlan(id="p1", name="Test Plan")
        event = DrPlanCreated(plan=plan)
        assert event.event_type == "dr.plan.created"
        assert event.plan.id == "p1"
        assert isinstance(event, DomainEvent)

    def test_dr_plan_activated(self) -> None:
        event = DrPlanActivated(plan_id="p1", plan_name="Test Plan")
        assert event.event_type == "dr.plan.activated"
        assert event.plan_id == "p1"

    def test_dr_plan_tested(self) -> None:
        result = DrTestResult(id="r1", plan_id="p1")
        event = DrPlanTested(plan_id="p1", result=result)
        assert event.event_type == "dr.plan.tested"
        assert event.result.id == "r1"

    def test_dr_plan_test_failed(self) -> None:
        event = DrPlanTestFailed(plan_id="p1", error="Step 2 failed")
        assert event.event_type == "dr.plan.test_failed"
        assert event.error == "Step 2 failed"

    def test_failover_started(self) -> None:
        fe = FailoverEvent(id="f1", plan_id="p1")
        event = FailoverStarted(event=fe)
        assert event.event_type == "dr.failover.started"
        assert event.event.id == "f1"

    def test_failover_completed(self) -> None:
        fe = FailoverEvent(id="f1", plan_id="p1")
        event = FailoverCompleted(event=fe)
        assert event.event_type == "dr.failover.completed"

    def test_failover_rolled_back(self) -> None:
        fe = FailoverEvent(id="f1", plan_id="p1")
        event = FailoverRolledBack(event=fe)
        assert event.event_type == "dr.failover.rolled_back"

    def test_failover_failed(self) -> None:
        fe = FailoverEvent(id="f1", plan_id="p1")
        event = FailoverFailed(event=fe, error="Timeout")
        assert event.event_type == "dr.failover.failed"
        assert event.error == "Timeout"

    def test_rto_rpo_violation(self) -> None:
        event = RtoRpoViolation(
            plan_id="p1",
            plan_name="Test Plan",
            rto_seconds=3600,
            rpo_seconds=900,
            actual_seconds=4500.0,
            violation_type="rto",
        )
        assert event.event_type == "dr.violation"
        assert event.violation_type == "rto"
        assert event.actual_seconds == 4500.0

    def test_all_events_are_frozen(self) -> None:
        result = DrTestResult(id="r1", plan_id="p1")
        event = DrPlanTested(plan_id="p1", result=result)
        with pytest.raises(ValidationError):
            event.plan_id = "changed"

    def test_event_type_uniqueness(self) -> None:
        types = [
            DrPlanCreated,
            DrPlanActivated,
            DrPlanTested,
            DrPlanTestFailed,
            FailoverStarted,
            FailoverCompleted,
            FailoverRolledBack,
            FailoverFailed,
            RtoRpoViolation,
        ]
        event_types = {cls.event_type for cls in types}
        assert len(event_types) == len(types), "Duplicate event types detected"
