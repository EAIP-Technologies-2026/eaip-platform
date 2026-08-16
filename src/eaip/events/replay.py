"""Event replay — re-dispatch persisted events from the durable event log.

BATCH 01 (Point 03) requires that historical events can be replayed from the
persistent store.  ``EventReplay`` reads from the PostgreSQL-backed event log
(via :class:`~eaip.events.store_pg.PgEventStore`) and re-invokes a caller
provided handler for each stored event.

Safety:

- Replay is **idempotent** for the store: it never mutates the log.  Handlers
  must tolerate duplicate delivery (the same principle the event bus already
  relies on).
- Tenant isolation is preserved — ``replay_for_tenant`` only reads events that
  belong to that tenant.
- An optional rate limit prevents a large replay from saturating the process.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from eaip.events.store_pg import PgEventStore
from eaip.logging.context import get_logger

log = get_logger("eaip.events.replay")

ReplayHandler = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass(slots=True)
class ReplayResult:
    """Summary of a replay run."""

    total: int = 0
    dispatched: int = 0
    failed: int = 0
    duration_ms: float = 0.0
    failures: list[tuple[str, str]] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.failed == 0


class EventReplay:
    """Replays persisted events through a caller-supplied handler."""

    def __init__(
        self,
        store: PgEventStore | None = None,
        *,
        max_events_per_second: float = 0.0,
    ) -> None:
        self._store = store or PgEventStore()
        self._rps = max(0.0, max_events_per_second)

    async def replay_since(self, since: datetime, handler: ReplayHandler) -> ReplayResult:
        """Replay every stored event created at or after ``since``."""
        events = await self._store.stored_events(since=since)
        return await self._run(events, handler)

    async def replay_range(
        self, start: datetime, end: datetime, handler: ReplayHandler
    ) -> ReplayResult:
        """Replay every stored event created within ``[start, end]``."""
        events = await self._store.stored_events(since=start, until=end)
        return await self._run(events, handler)

    async def replay_by_type(
        self, event_type: str, handler: ReplayHandler, *, since: datetime | None = None
    ) -> ReplayResult:
        """Replay every stored event of ``event_type`` (optionally since ``since``)."""
        events = await self._store.stored_events(event_type=event_type, since=since)
        return await self._run(events, handler)

    async def replay_for_tenant(
        self, tenant_id: str, handler: ReplayHandler, *, since: datetime | None = None
    ) -> ReplayResult:
        """Replay every stored event belonging to ``tenant_id`` (isolation-safe)."""
        events = await self._store.stored_events(tenant_id=tenant_id, since=since)
        return await self._run(events, handler)

    async def _run(self, events: list[dict[str, Any]], handler: ReplayHandler) -> ReplayResult:
        result = ReplayResult(total=len(events))
        start = time.monotonic()
        for idx, event in enumerate(events):
            if self._rps > 0 and idx > 0 and idx % int(self._rps) == 0:
                await asyncio.sleep(1.0)
            try:
                await handler(event)
                result.dispatched += 1
            except BaseException as exc:  # noqa: BLE001
                result.failed += 1
                result.failures.append((event.get("id", ""), repr(exc)))
                log.error(
                    "replay.handler_failed",
                    event_id=event.get("id"),
                    event_type=event.get("event_type"),
                    error=repr(exc),
                )
        result.duration_ms = round((time.monotonic() - start) * 1000, 3)
        log.info(
            "replay.completed",
            total=result.total,
            dispatched=result.dispatched,
            failed=result.failed,
            duration_ms=result.duration_ms,
        )
        return result


__all__ = ["EventReplay", "ReplayHandler", "ReplayResult"]