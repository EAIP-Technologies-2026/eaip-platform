"""Tests for workforce models."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.shared.time import utc_now
from eaip.workforce.models import (
    AssignmentStatus,
    WorkerAssignment,
    WorkerDefinition,
    WorkerType,
    WorkforceConfig,
    WorkforceMetrics,
)


class TestAssignmentStatus:
    def test_values(self) -> None:
        assert AssignmentStatus.PENDING == "pending"
        assert AssignmentStatus.RUNNING == "running"
        assert AssignmentStatus.COMPLETED == "completed"
        assert AssignmentStatus.FAILED == "failed"

    def test_valid_members(self) -> None:
        assert len(AssignmentStatus) == 4


class TestWorkerType:
    def test_values(self) -> None:
        assert WorkerType.AGENT == "agent"
        assert WorkerType.WORKFLOW == "workflow"
        assert WorkerType.JOB == "job"

    def test_valid_members(self) -> None:
        assert len(WorkerType) == 3


class TestWorkerDefinition:
    def test_defaults(self) -> None:
        w = WorkerDefinition(id="w1", name="Test Worker", worker_type=WorkerType.AGENT)
        assert w.id == "w1"
        assert w.name == "Test Worker"
        assert w.worker_type is WorkerType.AGENT
        assert w.agent_id == ""
        assert w.workflow_id == ""
        assert w.job_id == ""
        assert w.description == ""
        assert w.tags == ()
        assert w.metadata == {}
        assert w.max_concurrent_runs == 1
        assert w.timeout_seconds == 0.0

    def test_agent_worker(self) -> None:
        w = WorkerDefinition(
            id="w2",
            name="Sentiment Analyzer",
            worker_type=WorkerType.AGENT,
            agent_id="agent_sentiment_01",
            description="Analyzes sentiment of input text",
            tags=("nlp", "analysis"),
            metadata={"model": "gpt-4"},
            max_concurrent_runs=5,
            timeout_seconds=120.0,
        )
        assert w.agent_id == "agent_sentiment_01"
        assert w.description == "Analyzes sentiment of input text"
        assert w.tags == ("nlp", "analysis")
        assert w.metadata == {"model": "gpt-4"}
        assert w.max_concurrent_runs == 5
        assert w.timeout_seconds == 120.0

    def test_workflow_worker(self) -> None:
        w = WorkerDefinition(
            id="w3",
            name="Onboarding Flow",
            worker_type=WorkerType.WORKFLOW,
            workflow_id="wf_onboard_01",
        )
        assert w.workflow_id == "wf_onboard_01"
        assert w.worker_type is WorkerType.WORKFLOW

    def test_job_worker(self) -> None:
        w = WorkerDefinition(
            id="w4",
            name="Data Sync",
            worker_type=WorkerType.JOB,
            job_id="job_sync_01",
        )
        assert w.job_id == "job_sync_01"
        assert w.worker_type is WorkerType.JOB

    def test_frozen(self) -> None:
        w = WorkerDefinition(id="w1", name="Test", worker_type=WorkerType.AGENT)
        with pytest.raises(ValueError):
            w.name = "Changed"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValueError):
            WorkerDefinition(id="w1", name="Test", worker_type=WorkerType.AGENT, extra_field="x")  # type: ignore[call-arg]


class TestWorkerAssignment:
    def test_defaults(self) -> None:
        a = WorkerAssignment(id="a1", worker_id="w1", task_description="Do something")
        assert a.status is AssignmentStatus.PENDING
        assert isinstance(a.assigned_at, datetime)
        assert a.completed_at is None
        assert a.result == ""
        assert a.error is None
        assert a.run_id == ""
        assert a.priority == 0

    def test_completed(self) -> None:
        now = utc_now()
        a = WorkerAssignment(
            id="a2",
            worker_id="w1",
            task_description="Analyze data",
            status=AssignmentStatus.COMPLETED,
            completed_at=now,
            result="success",
            run_id="run_123",
            priority=50,
        )
        assert a.status is AssignmentStatus.COMPLETED
        assert a.completed_at == now
        assert a.result == "success"
        assert a.run_id == "run_123"
        assert a.priority == 50

    def test_failed(self) -> None:
        a = WorkerAssignment(
            id="a3",
            worker_id="w2",
            task_description="Process batch",
            status=AssignmentStatus.FAILED,
            error="timeout",
        )
        assert a.status is AssignmentStatus.FAILED
        assert a.error == "timeout"

    def test_frozen(self) -> None:
        a = WorkerAssignment(id="a1", worker_id="w1", task_description="Do it")
        with pytest.raises(ValueError):
            a.status = AssignmentStatus.RUNNING  # type: ignore[misc]


class TestWorkforceConfig:
    def test_defaults(self) -> None:
        c = WorkforceConfig()
        assert c.max_concurrent_workers == 10
        assert c.default_timeout_seconds == 300.0
        assert c.enable_auto_scaling is False
        assert c.health_check_interval_seconds == 60.0

    def test_custom(self) -> None:
        c = WorkforceConfig(
            max_concurrent_workers=25,
            default_timeout_seconds=600.0,
            enable_auto_scaling=True,
            health_check_interval_seconds=30.0,
        )
        assert c.max_concurrent_workers == 25
        assert c.default_timeout_seconds == 600.0
        assert c.enable_auto_scaling is True
        assert c.health_check_interval_seconds == 30.0

    def test_frozen(self) -> None:
        c = WorkforceConfig()
        with pytest.raises(ValueError):
            c.max_concurrent_workers = 20  # type: ignore[misc]


class TestWorkforceMetrics:
    def test_defaults(self) -> None:
        m = WorkforceMetrics()
        assert m.total_assignments == 0
        assert m.active_assignments == 0
        assert m.completed_assignments == 0
        assert m.failed_assignments == 0
        assert m.avg_duration_ms == 0.0
        assert m.workers_registered == 0

    def test_custom(self) -> None:
        m = WorkforceMetrics(
            total_assignments=100,
            active_assignments=5,
            completed_assignments=90,
            failed_assignments=5,
            avg_duration_ms=1250.5,
            workers_registered=10,
        )
        assert m.total_assignments == 100
        assert m.active_assignments == 5
        assert m.completed_assignments == 90
        assert m.failed_assignments == 5
        assert m.avg_duration_ms == 1250.5
        assert m.workers_registered == 10

    def test_frozen(self) -> None:
        m = WorkforceMetrics()
        with pytest.raises(ValueError):
            m.total_assignments = 10  # type: ignore[misc]
