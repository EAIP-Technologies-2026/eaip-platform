"""RuntimeRegistry — live snapshot of all active runtime components.

Tracks agents, workflows, sessions, knowledge jobs, and background tasks
for observability, diagnostics, and health reporting.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.runtime.events import RuntimeHealthChanged, RuntimeStarted, RuntimeStopped


class RuntimeRegistry:
    """Central registry for runtime component tracking.

    Provides live snapshots of active agents, workflows, sessions,
    knowledge jobs, and background tasks.
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._started_at = time.monotonic()
        self._event_bus = event_bus
        self._health_status: str = "starting"

        # Counters
        self.active_agents: int = 0
        self.active_workflows: int = 0
        self.active_sessions: int = 0
        self.active_knowledge_jobs: int = 0
        self.background_tasks: int = 0
        self.event_throughput: int = 0
        self.events_published: int = 0

        self._log = get_logger("eaip.runtime.registry")

    # ── Lifecycle ────────────────────────────────────────────────────

    async def start(self) -> None:
        """Mark the runtime as started."""
        self._health_status = "healthy"
        if self._event_bus is not None:
            await self._event_bus.publish(RuntimeStarted())
        self._log.info("runtime.registry.started")

    async def stop(self) -> None:
        """Mark the runtime as stopped."""
        self._health_status = "stopped"
        uptime = time.monotonic() - self._started_at
        if self._event_bus is not None:
            await self._event_bus.publish(RuntimeStopped(uptime_seconds=uptime))
        self._log.info("runtime.registry.stopped", uptime_seconds=round(uptime, 2))

    # ── Component management ─────────────────────────────────────────

    def set_health(self, status: str, previous: str | None = None) -> None:
        """Update health status and publish event if changed."""
        old = self._health_status
        self._health_status = status
        if old != status and self._event_bus is not None:
            _ = asyncio.ensure_future(
                self._event_bus.publish(
                    RuntimeHealthChanged(previous_status=old, new_status=status)
                )
            )

    # ── Snapshot ─────────────────────────────────────────────────────

    def get_snapshot(self) -> dict[str, Any]:
        """Return a live snapshot of the runtime state."""
        return {
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
            "health_status": self._health_status,
            "active_agents": self.active_agents,
            "active_workflows": self.active_workflows,
            "active_sessions": self.active_sessions,
            "active_knowledge_jobs": self.active_knowledge_jobs,
            "background_tasks": self.background_tasks,
            "events_published": self.events_published,
        }

    def get_stats(self) -> dict[str, Any]:
        """Alias for get_snapshot used by diagnostics."""
        return self.get_snapshot()


__all__ = ["RuntimeRegistry"]
