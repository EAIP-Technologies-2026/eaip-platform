"""Tests for collaboration events."""

from __future__ import annotations

import pytest

from eaip.collaboration.events import (
    ApprovalCompleted,
    ApprovalRejected,
    ApprovalRequested,
    CollaborationEvent,
    CollaborationSessionCompleted,
    CollaborationSessionCreated,
    CollaborationSessionFailed,
    CollaborationSessionStarted,
    ConsensusReached,
    DelegationAccepted,
    DelegationRejected,
    DelegationRequested,
    StateUpdated,
    TaskAssigned,
    TaskCompleted,
    TaskFailed,
)
from eaip.collaboration.models import SessionStatus
from eaip.events.event import DomainEvent


class TestCollaborationSessionCreated:
    def test_fields(self) -> None:
        e = CollaborationSessionCreated(
            session_id="s1",
            name="Test",
            session_type="sequential",
            agent_count=3,
        )
        assert e.event_type == "eaip.collaboration.session.created"
        assert e.session_id == "s1"
        assert e.name == "Test"
        assert e.session_type == "sequential"
        assert e.agent_count == 3

    def test_is_domain_event(self) -> None:
        assert isinstance(CollaborationSessionCreated(session_id="s1", name="x", session_type="s", agent_count=0), DomainEvent)


class TestCollaborationSessionStarted:
    def test_fields(self) -> None:
        e = CollaborationSessionStarted(session_id="s1", name="Test", strategy="parallel")
        assert e.event_type == "eaip.collaboration.session.started"
        assert e.session_id == "s1"
        assert e.strategy == "parallel"


class TestCollaborationSessionCompleted:
    def test_fields(self) -> None:
        e = CollaborationSessionCompleted(
            session_id="s1",
            status=SessionStatus.COMPLETED,
            duration_ms=100.0,
            task_count=5,
            consensus_reached=True,
        )
        assert e.event_type == "eaip.collaboration.session.completed"
        assert e.status is SessionStatus.COMPLETED
        assert e.duration_ms == 100.0
        assert e.task_count == 5
        assert e.consensus_reached is True


class TestCollaborationSessionFailed:
    def test_fields(self) -> None:
        e = CollaborationSessionFailed(session_id="s1", error="timeout", duration_ms=50.0)
        assert e.event_type == "eaip.collaboration.session.failed"
        assert e.error == "timeout"
        assert e.duration_ms == 50.0


class TestTaskAssigned:
    def test_fields(self) -> None:
        e = TaskAssigned(
            task_id="t1",
            session_id="s1",
            agent_id="a1",
            task_type="analysis",
            description="Analyze",
        )
        assert e.event_type == "eaip.collaboration.task.assigned"
        assert e.task_id == "t1"
        assert e.agent_id == "a1"
        assert e.task_type == "analysis"


class TestTaskCompleted:
    def test_fields(self) -> None:
        e = TaskCompleted(
            task_id="t1",
            session_id="s1",
            agent_id="a1",
            duration_ms=200.0,
            output="done",
        )
        assert e.event_type == "eaip.collaboration.task.completed"
        assert e.duration_ms == 200.0
        assert e.output == "done"


class TestTaskFailed:
    def test_fields(self) -> None:
        e = TaskFailed(task_id="t1", session_id="s1", agent_id="a1", error="crash")
        assert e.event_type == "eaip.collaboration.task.failed"
        assert e.error == "crash"


class TestDelegationRequested:
    def test_fields(self) -> None:
        e = DelegationRequested(
            delegation_id="d1",
            from_agent_id="a1",
            to_agent_id="a2",
            task_description="Do it",
        )
        assert e.event_type == "eaip.collaboration.delegation.requested"
        assert e.from_agent_id == "a1"
        assert e.to_agent_id == "a2"


class TestDelegationAccepted:
    def test_fields(self) -> None:
        e = DelegationAccepted(delegation_id="d1", to_agent_id="a2")
        assert e.event_type == "eaip.collaboration.delegation.accepted"
        assert e.delegation_id == "d1"


class TestDelegationRejected:
    def test_fields(self) -> None:
        e = DelegationRejected(delegation_id="d1", to_agent_id="a2", reason="busy")
        assert e.event_type == "eaip.collaboration.delegation.rejected"
        assert e.reason == "busy"


class TestApprovalRequested:
    def test_fields(self) -> None:
        e = ApprovalRequested(
            approval_id="ap1",
            session_id="s1",
            step_id="step1",
            approver_count=2,
        )
        assert e.event_type == "eaip.collaboration.approval.requested"
        assert e.approval_id == "ap1"
        assert e.approver_count == 2


class TestApprovalCompleted:
    def test_fields(self) -> None:
        e = ApprovalCompleted(approval_id="ap1", approver_id="admin")
        assert e.event_type == "eaip.collaboration.approval.completed"
        assert e.approver_id == "admin"


class TestApprovalRejected:
    def test_fields(self) -> None:
        e = ApprovalRejected(approval_id="ap1", approver_id="admin", reason="bad")
        assert e.event_type == "eaip.collaboration.approval.rejected"
        assert e.reason == "bad"


class TestStateUpdated:
    def test_fields(self) -> None:
        e = StateUpdated(session_id="s1", key="status", agent_id="a1", version=3)
        assert e.event_type == "eaip.collaboration.state.updated"
        assert e.key == "status"
        assert e.version == 3


class TestConsensusReached:
    def test_fields(self) -> None:
        e = ConsensusReached(session_id="s1", threshold=0.8, agreement_count=4, total_agents=5)
        assert e.event_type == "eaip.collaboration.consensus.reached"
        assert e.threshold == 0.8
        assert e.agreement_count == 4
        assert e.total_agents == 5


class TestCollaborationEvent:
    def test_union_type(self) -> None:
        events = [
            CollaborationSessionCreated(session_id="s1", name="x", session_type="s", agent_count=0),
            CollaborationSessionStarted(session_id="s1", name="x", strategy="s"),
            TaskAssigned(task_id="t1", session_id="s1", agent_id="a1"),
            DelegationRequested(delegation_id="d1", from_agent_id="a1", to_agent_id="a2"),
            ApprovalRequested(approval_id="ap1", session_id="s1", step_id="st1"),
            StateUpdated(session_id="s1", key="k", agent_id="a1", version=1),
            ConsensusReached(session_id="s1", threshold=0.5, agreement_count=1, total_agents=1),
        ]
        for event in events:
            assert isinstance(event, DomainEvent), f"{type(event).__name__} is not a DomainEvent"
            assert hasattr(event, "event_type")
            assert hasattr(event, "occurred_at")
