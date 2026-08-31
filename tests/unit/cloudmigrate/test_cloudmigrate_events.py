"""Tests for cloud migration domain events."""

from __future__ import annotations

import pydantic
import pytest

from eaip.cloudmigrate.events import (
    AssessmentCreated,
    MigrationCompleted,
    MigrationFailed,
    MigrationStarted,
    PlanApproved,
)


class TestAssessmentCreated:
    def test_create(self) -> None:
        event = AssessmentCreated(assessment_id="a1", source="aws", target="azure")
        assert event.assessment_id == "a1"
        assert event.source == "aws"
        assert event.target == "azure"
        assert event.event_type == "eaip.cloudmigrate.assessment_created"


class TestPlanApproved:
    def test_create(self) -> None:
        event = PlanApproved(plan_id="p1", assessment_id="a1")
        assert event.plan_id == "p1"
        assert event.assessment_id == "a1"
        assert event.event_type == "eaip.cloudmigrate.plan_approved"


class TestMigrationStarted:
    def test_create(self) -> None:
        event = MigrationStarted(plan_id="p1", total_tasks=5)
        assert event.plan_id == "p1"
        assert event.total_tasks == 5
        assert event.event_type == "eaip.cloudmigrate.migration_started"


class TestMigrationCompleted:
    def test_create(self) -> None:
        event = MigrationCompleted(plan_id="p1", completed_tasks=5, duration_seconds=120.5)
        assert event.completed_tasks == 5
        assert event.duration_seconds == 120.5
        assert event.event_type == "eaip.cloudmigrate.migration_completed"


class TestMigrationFailed:
    def test_create(self) -> None:
        event = MigrationFailed(plan_id="p1", failed_task="t1", reason="timeout")
        assert event.failed_task == "t1"
        assert event.reason == "timeout"
        assert event.event_type == "eaip.cloudmigrate.migration_failed"

    def test_frozen(self) -> None:
        event = MigrationFailed(plan_id="p1", failed_task="t1", reason="timeout")
        with pytest.raises(pydantic.ValidationError):
            event.reason = "other"  # type: ignore[misc]
