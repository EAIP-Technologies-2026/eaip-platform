"""Tests for collaboration models."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.collaboration.models import (
    AgentTask,
    CollaborationResult,
    CollaborationSession,
    CoordinationConfig,
    DelegationRequest,
    ErrorStrategy,
    SharedState,
)
from eaip.collaboration.models import (
    CoordinationStrategy as CS,
)
from eaip.collaboration.models import (
    DelegationStatus,
    SessionStatus,
    SessionType,
    TaskStatus,
)
from eaip.shared.time import utc_now


class TestCollaborationSession:
    def test_defaults(self) -> None:
        s = CollaborationSession(id="s1", name="Test Session", type=SessionType.SEQUENTIAL)
        assert s.id == "s1"
        assert s.name == "Test Session"
        assert s.type is SessionType.SEQUENTIAL
        assert s.status is SessionStatus.PENDING
        assert isinstance(s.created_at, datetime)
        assert isinstance(s.updated_at, datetime)
        assert s.agents == ()
        assert s.coordinator_agent_id == ""
        assert s.context == {}
        assert s.metadata == {}
        assert s.max_rounds == 1
        assert s.timeout_seconds == 0.0

    def test_parallel_session(self) -> None:
        s = CollaborationSession(
            id="s2",
            name="Parallel Session",
            type=SessionType.PARALLEL,
            agents=("agent_a", "agent_b"),
            coordinator_agent_id="agent_a",
            context={"input": "data"},
            metadata={"env": "test"},
            max_rounds=3,
            timeout_seconds=60.0,
        )
        assert s.type is SessionType.PARALLEL
        assert s.agents == ("agent_a", "agent_b")
        assert s.coordinator_agent_id == "agent_a"
        assert s.context == {"input": "data"}
        assert s.metadata == {"env": "test"}
        assert s.max_rounds == 3
        assert s.timeout_seconds == 60.0

    def test_broadcast_session(self) -> None:
        s = CollaborationSession(
            id="s3",
            name="Broadcast",
            type=SessionType.BROADCAST,
            agents=("a1", "a2", "a3"),
        )
        assert s.type is SessionType.BROADCAST
        assert len(s.agents) == 3

    def test_auction_session(self) -> None:
        s = CollaborationSession(
            id="s4",
            name="Auction",
            type=SessionType.AUCTION,
        )
        assert s.type is SessionType.AUCTION

    def test_status_transitions(self) -> None:
        s = CollaborationSession(id="s1", name="S", type=SessionType.SEQUENTIAL)
        assert s.status is SessionStatus.PENDING
        active = s.model_copy(update={"status": SessionStatus.ACTIVE})
        assert active.status is SessionStatus.ACTIVE
        completed = active.model_copy(update={"status": SessionStatus.COMPLETED})
        assert completed.status is SessionStatus.COMPLETED

    def test_frozen(self) -> None:
        s = CollaborationSession(id="s1", name="S", type=SessionType.SEQUENTIAL)
        with pytest.raises(ValueError):
            s.name = "Changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValueError):
            CollaborationSession(id="x", name="X", type=SessionType.SEQUENTIAL, extra="bad")


class TestAgentTask:
    def test_defaults(self) -> None:
        t = AgentTask(id="t1", session_id="s1", agent_id="a1")
        assert t.task_type == ""
        assert t.description == ""
        assert t.input_data == {}
        assert t.status is TaskStatus.PENDING
        assert t.priority == 0
        assert t.assigned_at is None
        assert t.started_at is None
        assert t.completed_at is None
        assert t.output == ""
        assert t.error is None
        assert t.duration_ms == 0.0
        assert t.depends_on == ()
        assert t.metadata == {}

    def test_full_task(self) -> None:
        now = utc_now()
        t = AgentTask(
            id="t2",
            session_id="s1",
            agent_id="a1",
            task_type="analysis",
            description="Analyze data",
            input_data={"source": "db"},
            status=TaskStatus.COMPLETED,
            priority=10,
            assigned_at=now,
            started_at=now,
            completed_at=now,
            output="result ok",
            duration_ms=150.0,
            depends_on=("t1",),
            metadata={"model": "gpt-4"},
        )
        assert t.task_type == "analysis"
        assert t.description == "Analyze data"
        assert t.input_data == {"source": "db"}
        assert t.status is TaskStatus.COMPLETED
        assert t.priority == 10
        assert t.assigned_at == now
        assert t.started_at == now
        assert t.completed_at == now
        assert t.output == "result ok"
        assert t.duration_ms == 150.0
        assert t.depends_on == ("t1",)
        assert t.metadata == {"model": "gpt-4"}

    def test_status_values(self) -> None:
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.ASSIGNED == "assigned"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.SKIPPED == "skipped"

    def test_frozen(self) -> None:
        t = AgentTask(id="t1", session_id="s1", agent_id="a1")
        with pytest.raises(ValueError):
            t.status = TaskStatus.RUNNING


class TestDelegationRequest:
    def test_defaults(self) -> None:
        d = DelegationRequest(id="d1", from_agent_id="a1", to_agent_id="a2")
        assert d.task_description == ""
        assert d.context == {}
        assert d.priority == 0
        assert d.deadline is None
        assert d.status is DelegationStatus.PENDING
        assert d.response == ""
        assert isinstance(d.created_at, datetime)

    def test_full_request(self) -> None:
        deadline = utc_now()
        d = DelegationRequest(
            id="d2",
            from_agent_id="a1",
            to_agent_id="a2",
            task_description="Process batch",
            context={"batch_id": "b1"},
            priority=5,
            deadline=deadline,
            status=DelegationStatus.ACCEPTED,
            response="will do",
        )
        assert d.task_description == "Process batch"
        assert d.context == {"batch_id": "b1"}
        assert d.priority == 5
        assert d.deadline == deadline
        assert d.status is DelegationStatus.ACCEPTED
        assert d.response == "will do"

    def test_frozen(self) -> None:
        d = DelegationRequest(id="d1", from_agent_id="a1", to_agent_id="a2")
        with pytest.raises(ValueError):
            d.status = DelegationStatus.ACCEPTED


class TestCoordinationConfig:
    def test_defaults(self) -> None:
        c = CoordinationConfig()
        assert c.strategy is CS.SEQUENTIAL
        assert c.max_rounds == 1
        assert c.timeout_seconds == 0.0
        assert c.require_consensus is False
        assert c.consensus_threshold == 1.0
        assert c.error_strategy is ErrorStrategy.ABORT

    def test_consensus_config(self) -> None:
        c = CoordinationConfig(
            strategy=CS.CONSENSUS,
            max_rounds=5,
            timeout_seconds=120.0,
            require_consensus=True,
            consensus_threshold=0.75,
            error_strategy=ErrorStrategy.CONTINUE,
        )
        assert c.strategy is CS.CONSENSUS
        assert c.max_rounds == 5
        assert c.timeout_seconds == 120.0
        assert c.require_consensus is True
        assert c.consensus_threshold == 0.75
        assert c.error_strategy is ErrorStrategy.CONTINUE

    def test_parallel_config(self) -> None:
        c = CoordinationConfig(
            strategy=CS.PARALLEL,
            error_strategy=ErrorStrategy.ISOLATION,
        )
        assert c.strategy is CS.PARALLEL
        assert c.error_strategy is ErrorStrategy.ISOLATION

    def test_frozen(self) -> None:
        c = CoordinationConfig()
        with pytest.raises(ValueError):
            c.strategy = CS.PARALLEL


class TestCollaborationResult:
    def test_defaults(self) -> None:
        r = CollaborationResult(session_id="s1", status=SessionStatus.COMPLETED)
        assert r.task_results == ()
        assert r.agent_count == 0
        assert r.total_duration_ms == 0.0
        assert r.consensus_reached is False
        assert r.output_summary == ""

    def test_full_result(self) -> None:
        t = AgentTask(id="t1", session_id="s1", agent_id="a1", status=TaskStatus.COMPLETED)
        r = CollaborationResult(
            session_id="s1",
            status=SessionStatus.COMPLETED,
            task_results=(t,),
            agent_count=2,
            total_duration_ms=500.0,
            consensus_reached=True,
            output_summary="1 completed",
        )
        assert len(r.task_results) == 1
        assert r.agent_count == 2
        assert r.total_duration_ms == 500.0
        assert r.consensus_reached is True
        assert r.output_summary == "1 completed"

    def test_frozen(self) -> None:
        r = CollaborationResult(session_id="s1", status=SessionStatus.COMPLETED)
        with pytest.raises(ValueError):
            r.agent_count = 5


class TestSharedState:
    def test_defaults(self) -> None:
        s = SharedState(id="st1", session_id="s1")
        assert s.variables == {}
        assert s.agent_contributions == {}
        assert s.version == 1
        assert isinstance(s.updated_at, datetime)

    def test_with_data(self) -> None:
        s = SharedState(
            id="st2",
            session_id="s1",
            variables={"key": "value", "count": 42},
            agent_contributions={"a1": "analysis complete"},
            version=3,
        )
        assert s.variables == {"key": "value", "count": 42}
        assert s.agent_contributions == {"a1": "analysis complete"}
        assert s.version == 3

    def test_frozen(self) -> None:
        s = SharedState(id="st1", session_id="s1")
        with pytest.raises(ValueError):
            s.version = 2
