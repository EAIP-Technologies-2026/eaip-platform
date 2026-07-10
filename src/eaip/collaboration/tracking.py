"""Execution tracker — records session events and generates reports."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from eaip.logging.context import get_logger


class TrackingEvent:
    """An individual tracking event record."""

    def __init__(
        self,
        session_id: str,
        event_type: str,
        data: dict[str, Any],
        agent_id: str = "",
        timestamp: datetime | None = None,
    ) -> None:
        self.session_id = session_id
        self.event_type = event_type
        self.data = data
        self.agent_id = agent_id
        self.timestamp = timestamp or datetime.now()


class ExecutionTracker:
    """Tracks collaboration execution events and generates reports/metrics.

    Provides full session timelines and per-agent activity timelines.
    """

    def __init__(self) -> None:
        self._events: list[TrackingEvent] = []
        self._log = get_logger("eaip.collaboration.tracking")

    async def record_event(
        self,
        session_id: str,
        event_type: str,
        data: dict[str, Any],
        agent_id: str = "",
    ) -> None:
        """Record a tracking event.

        Args:
            session_id: The session ID.
            event_type: The event type string.
            data: Event data payload.
            agent_id: Optional agent ID associated with the event.
        """
        event = TrackingEvent(
            session_id=session_id,
            event_type=event_type,
            data=data,
            agent_id=agent_id,
        )
        self._events.append(event)
        self._log.debug("event.recorded", session_id=session_id, event_type=event_type)

    async def get_session_timeline(
        self,
        session_id: str,
    ) -> list[dict[str, Any]]:
        """Get the full timeline of events for a session.

        Args:
            session_id: The session ID.

        Returns:
            A chronological list of event dicts.
        """
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "data": e.data,
                "agent_id": e.agent_id,
            }
            for e in self._events
            if e.session_id == session_id
        ]

    async def get_agent_timeline(
        self,
        agent_id: str,
    ) -> list[dict[str, Any]]:
        """Get the timeline of events for a specific agent.

        Args:
            agent_id: The agent ID.

        Returns:
            A chronological list of event dicts.
        """
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "data": e.data,
                "session_id": e.session_id,
            }
            for e in self._events
            if e.agent_id == agent_id
        ]

    async def generate_report(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        """Generate an execution report for a session.

        Args:
            session_id: The session ID.

        Returns:
            A report dict with summary statistics.
        """
        session_events = [e for e in self._events if e.session_id == session_id]
        if not session_events:
            return {
                "session_id": session_id,
                "event_count": 0,
                "duration_ms": 0.0,
                "agents_involved": [],
                "event_types": {},
            }

        start_time = session_events[0].timestamp
        end_time = session_events[-1].timestamp
        duration_ms = (end_time - start_time).total_seconds() * 1000

        agents = list({e.agent_id for e in session_events if e.agent_id})
        event_types: dict[str, int] = {}
        for e in session_events:
            event_types[e.event_type] = event_types.get(e.event_type, 0) + 1

        return {
            "session_id": session_id,
            "event_count": len(session_events),
            "duration_ms": duration_ms,
            "agents_involved": agents,
            "event_types": event_types,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }

    async def get_metrics(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        """Get execution metrics for a session.

        Args:
            session_id: The session ID.

        Returns:
            A dict of metrics.
        """
        session_events = [e for e in self._events if e.session_id == session_id]
        if not session_events:
            return {"event_count": 0, "agents": 0, "duration_seconds": 0.0}

        agents = {e.agent_id for e in session_events if e.agent_id}
        errors = [e for e in session_events if "fail" in e.event_type.lower() or "error" in e.event_type.lower()]

        return {
            "event_count": len(session_events),
            "agents": len(agents),
            "error_count": len(errors),
            "duration_seconds": max(
                (e.timestamp - session_events[0].timestamp).total_seconds()
                for e in session_events
            ),
        }


__all__ = ["ExecutionTracker"]
