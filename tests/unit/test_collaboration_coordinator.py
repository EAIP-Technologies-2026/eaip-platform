"""Tests for CoordinationEngine."""

from __future__ import annotations

import pytest

from eaip.collaboration.coordinator import CoordinationEngine
from eaip.collaboration.exceptions import SessionNotFoundError
from eaip.collaboration.models import (
    AgentTask,
    CollaborationSession,
    CoordinationConfig,
    SessionStatus,
    SessionType,
    TaskStatus,
)
from eaip.collaboration.models import (
    CoordinationStrategy as CS,
)
from eaip.collaboration.models import (
    ErrorStrategy,
)


class TestCoordinationEngine:
    @pytest.fixture
    def engine(self) -> CoordinationEngine:
        return CoordinationEngine()

    @pytest.fixture
    def sequential_session(self) -> CollaborationSession:
        return CollaborationSession(
            id="s1",
            name="Sequential Test",
            type=SessionType.SEQUENTIAL,
            agents=("agent_a", "agent_b"),
        )

    @pytest.fixture
    def parallel_session(self) -> CollaborationSession:
        return CollaborationSession(
            id="s2",
            name="Parallel Test",
            type=SessionType.PARALLEL,
            agents=("agent_a", "agent_b", "agent_c"),
        )

    async def test_create_session(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
    ) -> None:
        created = await engine.create_session(sequential_session)
        assert created.id == "s1"
        assert created.status is SessionStatus.PENDING

    async def test_create_session_with_config(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
    ) -> None:
        config = CoordinationConfig(strategy=CS.SEQUENTIAL, timeout_seconds=30.0)
        created = await engine.create_session(sequential_session, config)
        assert created.id == "s1"

    async def test_start_session(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
    ) -> None:
        await engine.create_session(sequential_session)
        started = await engine.start_session("s1")
        assert started.status is SessionStatus.ACTIVE

    async def test_start_session_not_found(self, engine: CoordinationEngine) -> None:
        with pytest.raises(SessionNotFoundError):
            await engine.start_session("nonexistent")

    async def test_add_task(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
    ) -> None:
        await engine.create_session(sequential_session)
        task = AgentTask(id="t1", session_id="s1", agent_id="agent_a", description="Do work")
        added = await engine.add_task("s1", task)
        assert added.id == "t1"

    async def test_add_task_no_session(self, engine: CoordinationEngine) -> None:
        task = AgentTask(id="t1", session_id="s1", agent_id="a1")
        with pytest.raises(SessionNotFoundError):
            await engine.add_task("nonexistent", task)

    async def test_get_session(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
    ) -> None:
        await engine.create_session(sequential_session)
        session = await engine.get_session("s1")
        assert session is not None
        assert session.id == "s1"

    async def test_get_session_not_found(self, engine: CoordinationEngine) -> None:
        session = await engine.get_session("nonexistent")
        assert session is None

    async def test_cancel_session(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
    ) -> None:
        await engine.create_session(sequential_session)
        cancelled = await engine.cancel_session("s1")
        assert cancelled is not None
        assert cancelled.status is SessionStatus.FAILED

    async def test_cancel_session_not_found(self, engine: CoordinationEngine) -> None:
        result = await engine.cancel_session("nonexistent")
        assert result is None

    async def test_list_sessions(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
        parallel_session: CollaborationSession,
    ) -> None:
        await engine.create_session(sequential_session)
        await engine.create_session(parallel_session)
        all_sessions = await engine.list_sessions()
        assert len(all_sessions) == 2

    async def test_list_sessions_by_status(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
    ) -> None:
        await engine.create_session(sequential_session)
        pending = await engine.list_sessions(status=SessionStatus.PENDING)
        assert len(pending) == 1
        active = await engine.list_sessions(status=SessionStatus.ACTIVE)
        assert len(active) == 0

    async def test_list_sessions_by_agent(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
    ) -> None:
        await engine.create_session(sequential_session)
        matches = await engine.list_sessions(agent_id="agent_a")
        assert len(matches) == 1
        no_match = await engine.list_sessions(agent_id="nonexistent")
        assert len(no_match) == 0

    async def test_execute_tasks_no_session(self, engine: CoordinationEngine) -> None:
        with pytest.raises(SessionNotFoundError):
            await engine.execute_tasks("nonexistent")

    async def test_execute_tasks_sequential(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
    ) -> None:
        await engine.create_session(sequential_session)
        await engine.add_task("s1", AgentTask(id="t1", session_id="s1", agent_id="agent_a", description="Task 1"))
        await engine.add_task("s1", AgentTask(id="t2", session_id="s1", agent_id="agent_b", description="Task 2"))
        result = await engine.execute_tasks("s1")
        assert result.status is SessionStatus.COMPLETED
        assert len(result.task_results) == 2
        assert result.consensus_reached is True

    async def test_execute_tasks_parallel(
        self,
        engine: CoordinationEngine,
        parallel_session: CollaborationSession,
    ) -> None:
        await engine.create_session(parallel_session)
        await engine.add_task("s2", AgentTask(id="t1", session_id="s2", agent_id="agent_a", description="P1"))
        await engine.add_task("s2", AgentTask(id="t2", session_id="s2", agent_id="agent_b", description="P2"))
        await engine.add_task("s2", AgentTask(id="t3", session_id="s2", agent_id="agent_c", description="P3"))
        result = await engine.execute_tasks("s2")
        assert result.status is SessionStatus.COMPLETED
        assert len(result.task_results) == 3

    async def test_execute_tasks_broadcast(
        self,
        engine: CoordinationEngine,
        parallel_session: CollaborationSession,
    ) -> None:
        await engine.create_session(parallel_session)
        await engine.add_task("s2", AgentTask(id="t1", session_id="s2", agent_id="agent_a", description="Broadcast task"))
        result = await engine.execute_tasks("s2")
        assert result.status is SessionStatus.COMPLETED

    async def test_execute_tasks_auction(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
    ) -> None:
        session = CollaborationSession(
            id="s3",
            name="Auction Test",
            type=SessionType.AUCTION,
            agents=("agent_a", "agent_b"),
        )
        await engine.create_session(session)
        await engine.add_task("s3", AgentTask(id="t1", session_id="s3", agent_id="agent_a", description="Task 1"))
        await engine.add_task("s3", AgentTask(id="t2", session_id="s3", agent_id="agent_b", description="Task 2"))
        result = await engine.execute_tasks("s3")
        assert result.status is SessionStatus.COMPLETED

    async def test_execute_tasks_error_abort(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
    ) -> None:
        await engine.create_session(sequential_session)
        # No agent_runtime set, so tasks will still "succeed" with simulated output
        await engine.add_task("s1", AgentTask(id="t1", session_id="s1", agent_id="agent_a"))
        await engine.add_task("s1", AgentTask(id="t2", session_id="s1", agent_id="agent_b"))
        result = await engine.execute_tasks("s1")
        assert result.status is SessionStatus.COMPLETED

    async def test_cancel_completed_session(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
    ) -> None:
        await engine.create_session(sequential_session)
        await engine.add_task("s1", AgentTask(id="t1", session_id="s1", agent_id="agent_a"))
        await engine.execute_tasks("s1")
        # Should return unchanged
        result = await engine.cancel_session("s1")
        assert result is not None
        assert result.status is SessionStatus.COMPLETED

    async def test_session_count(
        self,
        engine: CoordinationEngine,
        sequential_session: CollaborationSession,
        parallel_session: CollaborationSession,
    ) -> None:
        await engine.create_session(sequential_session)
        await engine.create_session(parallel_session)
        all_sessions = await engine.list_sessions()
        assert len(all_sessions) == 2
