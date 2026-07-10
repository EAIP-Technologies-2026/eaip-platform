"""Coordination engine — manages multi-agent collaboration sessions."""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from eaip.collaboration.events import (
    CollaborationSessionCompleted,
    CollaborationSessionCreated,
    CollaborationSessionFailed,
    CollaborationSessionStarted,
    ConsensusReached,
    TaskAssigned,
    TaskCompleted,
    TaskFailed,
)
from eaip.collaboration.exceptions import (
    ConsensusNotReachedError,
    SessionNotFoundError,
    TaskAssignmentError,
)
from eaip.collaboration.models import (
    AgentTask,
    CollaborationResult,
    CollaborationSession,
    CoordinationConfig,
    CoordinationStrategy,
    SessionStatus,
    SessionType,
    TaskStatus,
)
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.agents.runtime import AgentRuntime


class CoordinationEngine:
    """Orchestrates multi-agent collaboration sessions.

    Supports sequential, parallel, broadcast, and auction strategies.
    Integrates with AgentRuntime for task execution.
    """

    def __init__(
        self,
        agent_runtime: Any | None = None,
        event_bus: Any | None = None,
    ) -> None:
        self._agent_runtime: Any | None = agent_runtime
        self._event_bus: Any | None = event_bus
        self._sessions: dict[str, CollaborationSession] = {}
        self._tasks: dict[str, dict[str, AgentTask]] = {}
        self._configs: dict[str, CoordinationConfig] = {}
        self._log = get_logger("eaip.collaboration.coordinator")

    # ----------------------------------------------------------------
    # Session lifecycle
    # ----------------------------------------------------------------

    async def create_session(
        self,
        session: CollaborationSession,
        config: CoordinationConfig | None = None,
    ) -> CollaborationSession:
        """Create a new collaboration session.

        Args:
            session: The session to create.
            config: Optional coordination configuration.

        Returns:
            The created session.
        """
        self._sessions[session.id] = session
        self._tasks[session.id] = {}
        self._configs[session.id] = config or CoordinationConfig()

        self._publish(
            CollaborationSessionCreated(
                session_id=session.id,
                name=session.name,
                session_type=session.type,
                agent_count=len(session.agents),
            ),
        )
        self._log.info("session.created", session_id=session.id, name=session.name)
        return session

    async def start_session(self, session_id: str) -> CollaborationSession:
        """Start a pending collaboration session.

        Args:
            session_id: The session ID.

        Returns:
            The updated session.

        Raises:
            SessionNotFoundError: If the session does not exist.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        started = session.model_copy(update={
            "status": SessionStatus.ACTIVE,
            "updated_at": datetime.now(),
        })
        self._sessions[session_id] = started

        self._publish(
            CollaborationSessionStarted(
                session_id=session_id,
                name=session.name,
                strategy=session.type,
            ),
        )
        self._log.info("session.started", session_id=session_id)
        return started

    async def add_task(self, session_id: str, task: AgentTask) -> AgentTask:
        """Add a task to a collaboration session.

        Args:
            session_id: The session ID.
            task: The task to add.

        Returns:
            The added task.

        Raises:
            SessionNotFoundError: If the session does not exist.
        """
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)

        self._tasks[session_id][task.id] = task

        self._publish(
            TaskAssigned(
                task_id=task.id,
                session_id=session_id,
                agent_id=task.agent_id,
                task_type=task.task_type,
                description=task.description,
            ),
        )
        return task

    async def execute_tasks(self, session_id: str) -> CollaborationResult:
        """Execute all tasks in a session per the coordination strategy.

        Args:
            session_id: The session ID.

        Returns:
            The collaboration result.

        Raises:
            SessionNotFoundError: If the session does not exist.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        config = self._configs.get(session_id, CoordinationConfig())
        tasks = list(self._tasks.get(session_id, {}).values())

        t0 = time.monotonic()

        try:
            if session.type is SessionType.SEQUENTIAL:
                results = await self._execute_sequential(session, tasks, config)
            elif session.type is SessionType.PARALLEL:
                results = await self._execute_parallel(session, tasks, config)
            elif session.type is SessionType.BROADCAST:
                results = await self._execute_broadcast(session, tasks, config)
            elif session.type is SessionType.AUCTION:
                results = await self._execute_auction(session, tasks, config)

            total_duration = (time.monotonic() - t0) * 1000
            consensus = self._check_consensus(results, config)

            completed = session.model_copy(update={
                "status": SessionStatus.COMPLETED,
                "updated_at": datetime.now(),
            })
            self._sessions[session_id] = completed

            self._publish(
                CollaborationSessionCompleted(
                    session_id=session_id,
                    status=SessionStatus.COMPLETED,
                    duration_ms=total_duration,
                    task_count=len(results),
                    consensus_reached=consensus,
                ),
            )

            return CollaborationResult(
                session_id=session_id,
                status=SessionStatus.COMPLETED,
                task_results=tuple(results),
                agent_count=len(session.agents),
                total_duration_ms=total_duration,
                consensus_reached=consensus,
                output_summary=self._build_summary(results),
            )

        except Exception as exc:
            total_duration = (time.monotonic() - t0) * 1000
            failed = session.model_copy(update={
                "status": SessionStatus.FAILED,
                "updated_at": datetime.now(),
            })
            self._sessions[session_id] = failed

            self._publish(
                CollaborationSessionFailed(
                    session_id=session_id,
                    error=str(exc),
                    duration_ms=total_duration,
                ),
            )

            return CollaborationResult(
                session_id=session_id,
                status=SessionStatus.FAILED,
                task_results=(),
                agent_count=len(session.agents),
                total_duration_ms=total_duration,
                consensus_reached=False,
                output_summary=str(exc),
            )

    async def get_session(self, session_id: str) -> CollaborationSession | None:
        """Get the current status of a session.

        Args:
            session_id: The session ID.

        Returns:
            The session, or None if not found.
        """
        return self._sessions.get(session_id)

    async def cancel_session(self, session_id: str) -> CollaborationSession | None:
        """Cancel a collaboration session.

        Args:
            session_id: The session ID.

        Returns:
            The cancelled session, or None if not found.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.status in (SessionStatus.COMPLETED, SessionStatus.FAILED):
            return session

        cancelled = session.model_copy(update={
            "status": SessionStatus.FAILED,
            "updated_at": datetime.now(),
        })
        self._sessions[session_id] = cancelled
        self._log.info("session.cancelled", session_id=session_id)
        return cancelled

    async def list_sessions(
        self,
        status: SessionStatus | None = None,
        agent_id: str | None = None,
    ) -> list[CollaborationSession]:
        """List sessions, optionally filtered.

        Args:
            status: Optional status filter.
            agent_id: Optional agent ID filter.

        Returns:
            A list of matching sessions.
        """
        results = list(self._sessions.values())
        if status is not None:
            results = [s for s in results if s.status is status]
        if agent_id is not None:
            results = [s for s in results if agent_id in s.agents]
        return results

    # ----------------------------------------------------------------
    # Strategy implementations
    # ----------------------------------------------------------------

    async def _execute_sequential(
        self,
        session: CollaborationSession,
        tasks: list[AgentTask],
        config: CoordinationConfig,
    ) -> list[AgentTask]:
        results: list[AgentTask] = []
        for task in sorted(tasks, key=lambda t: t.priority, reverse=True):
            result = await self._execute_task(task, session)
            results.append(result)
            if result.status is TaskStatus.FAILED and config.error_strategy == "abort":
                self._skip_remaining(tasks, results)
                break
        return results

    async def _execute_parallel(
        self,
        session: CollaborationSession,
        tasks: list[AgentTask],
        config: CoordinationConfig,
    ) -> list[AgentTask]:
        coros = [self._execute_task(t, session) for t in tasks]
        completed = await asyncio.gather(*coros, return_exceptions=True)
        results: list[AgentTask] = []
        for i, r in enumerate(completed):
            if isinstance(r, Exception):
                failed = tasks[i].model_copy(update={
                    "status": TaskStatus.FAILED,
                    "error": str(r),
                })
                results.append(failed)
            elif isinstance(r, AgentTask):
                results.append(r)
        return results

    async def _execute_broadcast(
        self,
        session: CollaborationSession,
        tasks: list[AgentTask],
        config: CoordinationConfig,
    ) -> list[AgentTask]:
        # Broadcast: each agent gets the same task
        broadcast_task = tasks[0] if tasks else None
        if broadcast_task is None:
            return []

        agent_tasks: list[AgentTask] = []
        for agent_id in session.agents:
            agent_task = broadcast_task.model_copy(update={
                "id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "session_id": session.id,
            })
            agent_tasks.append(agent_task)
            self._tasks[session.id][agent_task.id] = agent_task

        coros = [self._execute_task(t, session) for t in agent_tasks]
        completed = await asyncio.gather(*coros, return_exceptions=True)
        results: list[AgentTask] = []
        for i, result in enumerate(completed):
            if isinstance(result, Exception):
                failed = agent_tasks[i].model_copy(update={
                    "status": TaskStatus.FAILED,
                    "error": str(result),
                })
                results.append(failed)
            elif isinstance(result, AgentTask):
                results.append(result)
        return results

    async def _execute_auction(
        self,
        session: CollaborationSession,
        tasks: list[AgentTask],
        config: CoordinationConfig,
    ) -> list[AgentTask]:
        # Auction: assign tasks to the best available agents
        available = list(session.agents)
        results: list[AgentTask] = []

        for task in sorted(tasks, key=lambda t: t.priority, reverse=True):
            if not available:
                skipped = task.model_copy(update={
                    "status": TaskStatus.SKIPPED,
                    "error": "no available agents",
                })
                results.append(skipped)
                continue

            # Pick the first available agent
            agent_id = available.pop(0)
            assigned = task.model_copy(update={
                "agent_id": agent_id,
                "status": TaskStatus.ASSIGNED,
                "assigned_at": datetime.now(),
            })
            self._tasks[session.id][task.id] = assigned
            result = await self._execute_task(assigned, session)
            results.append(result)

        return results

    # ----------------------------------------------------------------
    # Task execution helpers
    # ----------------------------------------------------------------

    async def _execute_task(
        self,
        task: AgentTask,
        session: CollaborationSession,
    ) -> AgentTask:
        running = task.model_copy(update={
            "status": TaskStatus.RUNNING,
            "started_at": datetime.now(),
        })
        self._tasks[session.id][task.id] = running

        t0 = time.monotonic()
        try:
            output = ""
            if self._agent_runtime is not None:
                run = await self._agent_runtime.create_run(
                    task.agent_id,
                    task.description or task.task_type,
                )
                result = await self._agent_runtime.start_run(run.id)
                output = result.result if hasattr(result, "result") else str(result)
            else:
                output = f"simulated: {task.description}"

            elapsed = (time.monotonic() - t0) * 1000
            completed = task.model_copy(update={
                "status": TaskStatus.COMPLETED,
                "output": output,
                "completed_at": datetime.now(),
                "duration_ms": elapsed,
            })
            self._tasks[session.id][task.id] = completed

            self._publish(
                TaskCompleted(
                    task_id=task.id,
                    session_id=session.id,
                    agent_id=task.agent_id,
                    duration_ms=elapsed,
                    output=output,
                ),
            )
            return completed

        except Exception as exc:
            elapsed = (time.monotonic() - t0) * 1000
            failed = task.model_copy(update={
                "status": TaskStatus.FAILED,
                "error": str(exc),
                "completed_at": datetime.now(),
                "duration_ms": elapsed,
            })
            self._tasks[session.id][task.id] = failed

            self._publish(
                TaskFailed(
                    task_id=task.id,
                    session_id=session.id,
                    agent_id=task.agent_id,
                    error=str(exc),
                ),
            )
            return failed

    def _skip_remaining(
        self,
        tasks: list[AgentTask],
        results: list[AgentTask],
    ) -> None:
        completed_ids = {t.id for t in results}
        for task in tasks:
            if task.id not in completed_ids:
                skipped = task.model_copy(update={
                    "status": TaskStatus.SKIPPED,
                    "error": "skipped due to earlier failure",
                })
                results.append(skipped)

    def _check_consensus(
        self,
        results: list[AgentTask],
        config: CoordinationConfig,
    ) -> bool:
        if not config.require_consensus:
            return True
        completed = [t for t in results if t.status is TaskStatus.COMPLETED]
        if not completed:
            return False
        agreement = sum(1 for t in completed if t.output.strip())
        ratio = agreement / len(results)
        return ratio >= config.consensus_threshold

    def _build_summary(self, results: list[AgentTask]) -> str:
        completed = sum(1 for t in results if t.status is TaskStatus.COMPLETED)
        failed = sum(1 for t in results if t.status is TaskStatus.FAILED)
        skipped = sum(1 for t in results if t.status is TaskStatus.SKIPPED)
        return f"{completed} completed, {failed} failed, {skipped} skipped"

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            try:
                self._event_bus.publish(event)
            except Exception:
                self._log.warning("event.publish.failed", event_type=type(event).__name__)


__all__ = ["CoordinationEngine"]
