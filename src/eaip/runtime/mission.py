"""Mission — a coordinated unit of work spanning agents, knowledge, workflows, and automation.

A Mission orchestrates multiple EAIP subsystems toward a single goal,
with full lifecycle management, event publishing, and observability.
"""

from __future__ import annotations

import time
from enum import StrEnum
from typing import Any

from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.runtime.events import (
    MissionCancelled,
    MissionCompleted,
    MissionCreated,
    MissionFailed,
    MissionStarted,
)


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
    ) -> None:
        self.mission_id = mission_id
        self.name = name
        self._event_bus = event_bus
        self.agent_ids = agent_ids
        self.workflow_ids = workflow_ids
        self.knowledge_collections = knowledge_collections
        self.metadata = metadata or {}
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
        self._started_at = time.monotonic()
        await self._publish(MissionStarted(mission_id=self.mission_id))
        self._log.info("mission.started", mission_id=self.mission_id)

    async def complete(self, result: str = "") -> None:
        """Mark mission as completed successfully."""
        self.status = MissionStatus.COMPLETED
        self._completed_at = time.monotonic()
        self._result = result
        duration_ms = self.duration_ms
        await self._publish(
            MissionCompleted(mission_id=self.mission_id, duration_ms=duration_ms, result=result)
        )
        self._log.info("mission.completed", mission_id=self.mission_id, duration_ms=duration_ms)

    async def fail(self, error: str) -> None:
        """Mark mission as failed."""
        self.status = MissionStatus.FAILED
        self._completed_at = time.monotonic()
        self._error = error
        await self._publish(MissionFailed(mission_id=self.mission_id, error=error))
        self._log.error("mission.failed", mission_id=self.mission_id, error=error)

    async def cancel(self) -> None:
        """Cancel mission execution."""
        self.status = MissionStatus.CANCELLED
        self._completed_at = time.monotonic()
        await self._publish(MissionCancelled(mission_id=self.mission_id))
        self._log.info("mission.cancelled", mission_id=self.mission_id)

    # ── Properties ──────────────────────────────────────────────────

    @property
    def duration_ms(self) -> float:
        if self._started_at is None:
            return 0.0
        end = self._completed_at or time.monotonic()
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

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._missions: dict[str, Mission] = {}
        self._event_bus = event_bus
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
        )
        self._missions[mission_id] = mission
        if self._event_bus is not None:
            await self._event_bus.publish(
                MissionCreated(mission_id=mission_id, name=name)
            )
        self._log.info("mission.created", mission_id=mission_id)
        return mission

    async def get(self, mission_id: str) -> Mission | None:
        return self._missions.get(mission_id)

    async def list_missions(
        self, status: MissionStatus | None = None
    ) -> list[Mission]:
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
            "success_rate": round(
                len(completed) / max(len(completed) + len(failed), 1) * 100, 1
            ),
        }


__all__ = ["Mission", "MissionRegistry", "MissionStatus"]
