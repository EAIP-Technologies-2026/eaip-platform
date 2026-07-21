"""Tests for DR models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.dr.models import (
    ComponentType,
    DrComponent,
    DrConfig,
    DrPlan,
    DrStep,
    DrTestResult,
    DrTestResultStatus,
    FailoverEvent,
    FailoverEventStatus,
    PlanPriority,
    PlanStatus,
    StepStatus,
    StepType,
)


class TestDrComponent:
    def test_minimal(self) -> None:
        c = DrComponent(id="comp_1", name="Primary Database", type=ComponentType.DATABASE)
        assert c.id == "comp_1"
        assert c.criticality == PlanPriority.MEDIUM
        assert c.max_allowed_downtime_seconds == 300

    def test_frozen(self) -> None:
        c = DrComponent(id="c1", name="Web Server", type=ComponentType.COMPUTE)
        with pytest.raises(ValidationError):
            c.name = "Changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            DrComponent(id="c1", name="Test", type=ComponentType.COMPUTE, unknown=True)

    def test_full(self) -> None:
        c = DrComponent(
            id="comp_db",
            name="Postgres Primary",
            type=ComponentType.DATABASE,
            criticality=PlanPriority.CRITICAL,
            backup_source="azcopy://backups/db",
            recovery_procedure="Restore from latest snapshot",
            max_allowed_downtime_seconds=120,
            metadata={"region": "eastus"},
        )
        assert c.criticality == PlanPriority.CRITICAL
        assert c.backup_source == "azcopy://backups/db"
        assert c.metadata["region"] == "eastus"


class TestDrStep:
    def test_minimal(self) -> None:
        s = DrStep(id="step_1", plan_id="plan_a", name="Verify backup")
        assert s.type == StepType.VERIFY
        assert s.status == StepStatus.PENDING
        assert s.timeout_seconds == 60

    def test_frozen(self) -> None:
        s = DrStep(id="s1", plan_id="p1", name="Step")
        with pytest.raises(ValidationError):
            s.name = "Changed"

    def test_required_steps(self) -> None:
        s = DrStep(
            id="step_2",
            plan_id="plan_a",
            name="Failover DB",
            type=StepType.FAILOVER,
            required_steps=("step_1",),
        )
        assert "step_1" in s.required_steps

    def test_all_step_types(self) -> None:
        for st in StepType:
            s = DrStep(id=f"s_{st.value}", plan_id="p", name=st.value, type=st)
            assert s.type == st


class TestDrPlan:
    def test_minimal(self) -> None:
        p = DrPlan(id="plan_1", name="East US DR")
        assert p.status == PlanStatus.DRAFT
        assert p.priority == PlanPriority.MEDIUM
        assert p.rto_seconds == 3600
        assert p.rpo_seconds == 900

    def test_frozen(self) -> None:
        p = DrPlan(id="p1", name="Plan")
        with pytest.raises(ValidationError):
            p.name = "Changed"

    def test_with_components_and_steps(self) -> None:
        comp = DrComponent(id="c1", name="Web", type=ComponentType.COMPUTE)
        step = DrStep(id="s1", plan_id="p1", name="Verify")
        p = DrPlan(
            id="p1",
            name="Full Plan",
            components=(comp,),
            steps=(step,),
        )
        assert len(p.components) == 1
        assert len(p.steps) == 1

    def test_status_transitions(self) -> None:
        for status in PlanStatus:
            p = DrPlan(id="p1", name="Plan", status=status)
            assert p.status == status

    def test_priority_levels(self) -> None:
        for pri in PlanPriority:
            p = DrPlan(id="p1", name="Plan", priority=pri)
            assert p.priority == pri


class TestDrTestResult:
    def test_minimal(self) -> None:
        r = DrTestResult(id="r1", plan_id="p1")
        assert r.status == DrTestResultStatus.PASSED
        assert r.steps_passed == 0
        assert r.findings == ()

    def test_partial(self) -> None:
        r = DrTestResult(
            id="r2",
            plan_id="p1",
            status=DrTestResultStatus.PARTIAL,
            steps_passed=3,
            steps_failed=1,
            steps_total=4,
            findings=("Step 2 failed",),
        )
        assert r.status == DrTestResultStatus.PARTIAL
        assert r.steps_failed == 1

    def test_frozen(self) -> None:
        r = DrTestResult(id="r1", plan_id="p1")
        with pytest.raises(ValidationError):
            r.status = DrTestResultStatus.FAILED


class TestFailoverEvent:
    def test_minimal(self) -> None:
        e = FailoverEvent(id="evt_1", plan_id="p1")
        assert e.status == FailoverEventStatus.PENDING

    def test_frozen(self) -> None:
        e = FailoverEvent(id="e1", plan_id="p1")
        with pytest.raises(ValidationError):
            e.reason = "changed"

    def test_all_statuses(self) -> None:
        for s in FailoverEventStatus:
            e = FailoverEvent(id="e1", plan_id="p1", status=s)
            assert e.status == s


class TestDrConfig:
    def test_defaults(self) -> None:
        c = DrConfig()
        assert c.auto_failover_enabled is False
        assert c.health_check_interval_seconds == 30
        assert c.max_retries == 3
        assert c.notify_on_failover is True
        assert c.failover_timeout_seconds == 600
        assert c.test_interval_days == 30

    def test_mutable(self) -> None:
        c = DrConfig()
        c.auto_failover_enabled = True
        assert c.auto_failover_enabled is True

    def test_custom_values(self) -> None:
        c = DrConfig(
            auto_failover_enabled=True,
            health_check_interval_seconds=60,
            max_retries=5,
            test_interval_days=7,
        )
        assert c.max_retries == 5
        assert c.test_interval_days == 7
