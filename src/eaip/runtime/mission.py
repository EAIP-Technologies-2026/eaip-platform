"""Mission — a coordinated unit of work spanning agents, knowledge, workflows, and automation.

A Mission orchestrates multiple EAIP subsystems toward a single goal,
with full lifecycle management, event publishing, and observability.
"""

from __future__ import annotations

import time
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.runtime.events import (
    MissionCancelled,
    MissionCompleted,
    MissionCreated,
    MissionFailed,
    MissionStarted,
)

if TYPE_CHECKING:
    pass


class MissionStatus(StrEnum):
    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Mission:
    """A single mission execution within the EAIP runtime.

    Tracks lifecycle, timing, and coordinates with agents, workflows,
    and knowledge subsystems via the event bus.
    """

    def __init__(
        self,
        mission_id: str,
        name: str,
        *,
        event_bus: EventBus | None = None,
        agent_ids: tuple[str, ...] = (),
        workflow_ids: tuple[str, ...] = (),
        knowledge_collections: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
        agent_runtime: Any | None = None,
        workflow_registry: Any | None = None,
        workflow_engine: Any | None = None,
    ) -> None:
        self.mission_id = mission_id
        self.name = name
        self._event_bus = event_bus
        self.agent_ids = agent_ids
        self.workflow_ids = workflow_ids
        self.knowledge_collections = knowledge_collections
        self.metadata = metadata or {}
        self._agent_runtime = agent_runtime
        self._workflow_registry = workflow_registry
        self._workflow_engine = workflow_engine
        self.status = MissionStatus.DRAFT
        self._started_at: float | None = None
        self._completed_at: float | None = None
        self._error: str | None = None
        self._result: str = ""
        self._log = get_logger("eaip.runtime.mission")

    # ── Lifecycle ────────────────────────────────────────────────────

    async def queue(self) -> None:
        """Transition mission to QUEUED status."""
        self.status = MissionStatus.QUEUED
        self._log.info("mission.queued", mission_id=self.mission_id)

    async def start(self) -> None:
        """Start mission execution."""
        self.status = MissionStatus.RUNNING
        self._started_at = time.time()
        await self._publish(MissionStarted(mission_id=self.mission_id))
        self._log.info("mission.started", mission_id=self.mission_id)

    async def complete(self, result: str = "") -> None:
        """Mark mission as completed successfully."""
        self.status = MissionStatus.COMPLETED
        self._completed_at = time.time()
        self._result = result
        duration_ms = self.duration_ms
        await self._publish(
            MissionCompleted(mission_id=self.mission_id, duration_ms=duration_ms, result=result)
        )
        self._log.info("mission.completed", mission_id=self.mission_id, duration_ms=duration_ms)

    async def fail(self, error: str) -> None:
        """Mark mission as failed."""
        self.status = MissionStatus.FAILED
        self._completed_at = time.time()
        self._error = error
        await self._publish(MissionFailed(mission_id=self.mission_id, error=error))
        self._log.error("mission.failed", mission_id=self.mission_id, error=error)

    async def cancel(self) -> None:
        """Cancel mission execution."""
        self.status = MissionStatus.CANCELLED
        self._completed_at = time.time()
        await self._publish(MissionCancelled(mission_id=self.mission_id))
        self._log.info("mission.cancelled", mission_id=self.mission_id)

    async def execute(self) -> None:
        """Execute this mission by running all referenced agents and workflows.

        Iterates agent_ids and invokes AgentRuntime for each, then
        iterates workflow_ids and invokes WorkflowEngine via WorkflowRegistry.
        Results are accumulated into the mission result string.
        """
        await self.start()
        results: list[str] = []

        if self._agent_runtime is not None:
            from eaip.agents.models import AgentSpec, Goal

            for agent_id in self.agent_ids:
                try:
                    spec = AgentSpec(id=agent_id, name=agent_id)
                    goal = Goal(text=self.name)
                    run = await self._agent_runtime.create_run(spec, goal)
                    completed = await self._agent_runtime.start_run(run.id)
                    results.append(f"agent:{agent_id} -> {completed.result or 'ok'}")
                except Exception as exc:
                    results.append(f"agent:{agent_id} -> error: {exc}")
                    self._log.warning("mission.agent.failed", agent_id=agent_id, error=str(exc))

        if self._workflow_engine is not None and self._workflow_registry is not None:
            for workflow_id in self.workflow_ids:
                try:
                    definition = await self._workflow_registry.get(workflow_id)
                    if definition is not None:
                        from eaip.workflow.models import WorkflowContext

                        ctx = WorkflowContext(variables={"mission_id": self.mission_id})
                        wf_result = await self._workflow_engine.execute(definition, ctx)
                        results.append(f"workflow:{workflow_id} -> {wf_result.status.value}")
                    else:
                        results.append(f"workflow:{workflow_id} -> not found")
                except Exception as exc:
                    results.append(f"workflow:{workflow_id} -> error: {exc}")
                    self._log.warning(
                        "mission.workflow.failed", workflow_id=workflow_id, error=str(exc)
                    )

        combined = "; ".join(results) if results else "no agents or workflows to execute"
        await self.complete(result=combined)

    # ── Properties ──────────────────────────────────────────────────

    @property
    def duration_ms(self) -> float:
        if self._started_at is None:
            return 0.0
        end = self._completed_at or time.time()
        return (end - self._started_at) * 1000

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def result(self) -> str:
        return self._result

    def to_dict(self) -> dict[str, Any]:
        """Return a snapshot of the mission state."""
        return {
            "mission_id": self.mission_id,
            "name": self.name,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "agent_ids": list(self.agent_ids),
            "workflow_ids": list(self.workflow_ids),
            "knowledge_collections": list(self.knowledge_collections),
            "error": self._error,
            "result": self._result,
        }

    async def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)


class MissionRegistry:
    """Registry of all missions in the runtime.

    Supports CRUD and provides aggregate statistics.
    """

    def __init__(
        self,
        event_bus: EventBus | None = None,
        agent_runtime: Any | None = None,
        workflow_registry: Any | None = None,
        workflow_engine: Any | None = None,
    ) -> None:
        self._missions: dict[str, Mission] = {}
        self._event_bus = event_bus
        self._agent_runtime = agent_runtime
        self._workflow_registry = workflow_registry
        self._workflow_engine = workflow_engine
        self._log = get_logger("eaip.runtime.mission_registry")

    async def create(
        self,
        mission_id: str,
        name: str,
        *,
        agent_ids: tuple[str, ...] = (),
        workflow_ids: tuple[str, ...] = (),
        knowledge_collections: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> Mission:
        """Create a new mission."""
        mission = Mission(
            mission_id=mission_id,
            name=name,
            event_bus=self._event_bus,
            agent_ids=agent_ids,
            workflow_ids=workflow_ids,
            knowledge_collections=knowledge_collections,
            metadata=metadata,
            agent_runtime=self._agent_runtime,
            workflow_registry=self._workflow_registry,
            workflow_engine=self._workflow_engine,
        )
        self._missions[mission_id] = mission
        if self._event_bus is not None:
            await self._event_bus.publish(MissionCreated(mission_id=mission_id, name=name))
        self._log.info("mission.created", mission_id=mission_id)
        return mission

    async def get(self, mission_id: str) -> Mission | None:
        return self._missions.get(mission_id)

    async def delete(self, mission_id: str) -> bool:
        if mission_id not in self._missions:
            return False
        del self._missions[mission_id]
        self._log.info("mission.deleted", mission_id=mission_id)
        return True

    async def list_missions(self, status: MissionStatus | None = None) -> list[Mission]:
        results = list(self._missions.values())
        if status is not None:
            results = [m for m in results if m.status == status]
        return results

    def get_stats(self) -> dict[str, Any]:
        """Return aggregate mission statistics."""
        all_missions = list(self._missions.values())
        completed = [m for m in all_missions if m.status == MissionStatus.COMPLETED]
        failed = [m for m in all_missions if m.status == MissionStatus.FAILED]
        running = [m for m in all_missions if m.status == MissionStatus.RUNNING]
        return {
            "total": len(all_missions),
            "running": len(running),
            "completed": len(completed),
            "failed": len(failed),
            "success_rate": round(len(completed) / max(len(completed) + len(failed), 1) * 100, 1),
        }


__all__ = ["Mission", "MissionRegistry", "MissionStatus"]
