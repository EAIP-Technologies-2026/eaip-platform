from __future__ import annotations

import re
from collections import deque
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from eaip.events.event import DomainEvent


def _camel_to_title(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name)


def _safe_dump(event: DomainEvent) -> dict[str, Any]:
    try:
        return event.model_dump()
    except Exception:
        return {}


class EventStore:
    def __init__(self, maxlen: int = 1000) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=maxlen)

    async def record(self, event: DomainEvent) -> None:
        activity = self._to_activity(event)
        data = _safe_dump(event)
        activity["_agent_id"] = data.get("agent_id")
        activity["_workflow_id"] = data.get("workflow_id")
        activity["_run_id"] = data.get("run_id")
        activity["_mission_id"] = data.get("mission_id")
        activity["_classified_type"] = self._classify(event)
        self._events.append(activity)

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        events = list(self._events)
        events.reverse()
        return [self._strip_internal(e) for e in events[:limit]]

    def recent_by(
        self,
        *,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        mission_id: str | None = None,
        type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        matching = list(self._events)
        if agent_id is not None:
            matching = [e for e in matching if e.get("_agent_id") == agent_id]
        if workflow_id is not None:
            matching = [e for e in matching if e.get("_workflow_id") == workflow_id]
        if mission_id is not None:
            matching = [e for e in matching if e.get("_mission_id") == mission_id]
        if type is not None:
            matching = [e for e in matching if e.get("_classified_type") == type]
        matching.reverse()
        return [self._strip_internal(e) for e in matching[:limit]]

    @staticmethod
    def _strip_internal(activity: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in activity.items() if not k.startswith("_")}

    def _classify(self, event: DomainEvent) -> str:
        module = type(event).__module__
        if "agents" in module:
            return "agent"
        if "workflow" in module:
            return "workflow"
        if "knowledge" in module:
            return "knowledge"
        if "auth" in module:
            return "auth"
        if "mission" in module:
            return "mission"
        return "system"

    @staticmethod
    def _determine_status(type_name: str) -> str:
        upper = type_name.upper()
        if any(w in upper for w in ["FAIL", "ERROR", "TIMEOUT"]):
            return "error"
        if any(w in upper for w in ["SUCCESS", "COMPLETE", "FINISHED"]):
            return "success"
        if any(w in upper for w in ["WARN", "DEGRADED"]):
            return "warning"
        return "info"

    @staticmethod
    def _build_message(event: DomainEvent) -> str:
        data = _safe_dump(event)

        skip_keys = {"occurred_at", "correlation_id", "event_type"}
        fields = {k: v for k, v in data.items() if k not in skip_keys and not k.startswith("_")}

        if not fields:
            return type(event).__name__

        parts = []
        for k, v in fields.items():
            if isinstance(v, (str, int, float, bool)):
                parts.append(f"{k}={v}")
            else:
                parts.append(f"{k}={type(v).__name__}")
        return ", ".join(parts[:5])

    def _to_activity(self, event: DomainEvent) -> dict[str, Any]:
        type_name = type(event).__name__
        occurred = getattr(event, "occurred_at", None)
        timestamp = (
            occurred.isoformat()
            if isinstance(occurred, datetime)
            else datetime.now(UTC).isoformat()
        )
        return {
            "id": str(uuid4()),
            "type": self._classify(event),
            "action": _camel_to_title(type_name),
            "message": self._build_message(event),
            "timestamp": timestamp,
            "status": self._determine_status(type_name),
        }
