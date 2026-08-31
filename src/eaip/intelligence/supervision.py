from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any

from eaip.intelligence.models import SupervisionRecord
from eaip.shared.time import utc_now
import uuid


class SupervisionEngine:
    def __init__(self, event_bus: Any | None = None) -> None:
        self._records: dict[str, SupervisionRecord] = {}
        self._action_history: dict[str, deque[str]] = defaultdict(lambda: deque(maxlen=10))
        self._progress_history: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=10))
        self._event_bus = event_bus

    def _key(self, tenant_id: str, record_id: str) -> str:
        return f"{tenant_id}:{record_id}"

    def track(self, tenant_id: str, agent_id: str, goal: str = "", mission_id: str = "", strategy: str = "direct") -> SupervisionRecord:
        record_id = f"sup-{uuid.uuid4().hex[:8]}"
        rec = SupervisionRecord(record_id=record_id, tenant_id=tenant_id, agent_id=agent_id, mission_id=mission_id, goal=goal, strategy=strategy)
        self._records[self._key(tenant_id, record_id)] = rec
        return rec

    def get(self, record_id: str, tenant_id: str) -> SupervisionRecord | None:
        return self._records.get(self._key(tenant_id, record_id))

    def list_for_tenant(self, tenant_id: str) -> list[SupervisionRecord]:
        return [v for k, v in self._records.items() if k.startswith(f"{tenant_id}:")]

    def update_progress(self, record_id: str, tenant_id: str, progress: float, confidence: float = 0, warnings: list[str] | None = None) -> SupervisionRecord | None:
        rec = self.get(record_id, tenant_id)
        if not rec:
            return None
        self._progress_history[record_id].append(progress)
        w = tuple(warnings or [])
        updated = rec.model_copy(update={"progress": progress, "confidence": confidence, "warnings": w, "updated_at": utc_now()})
        self._records[self._key(tenant_id, record_id)] = updated
        self._check_stagnation(record_id, tenant_id)
        return updated

    def record_action(self, record_id: str, tenant_id: str, action: str) -> None:
        self._action_history[record_id].append(action)
        self._check_loop(record_id, tenant_id)

    def _check_loop(self, record_id: str, tenant_id: str) -> bool:
        hist = list(self._action_history[record_id])
        if len(hist) >= 3 and hist[-1] == hist[-2] == hist[-3]:
            self._warn(record_id, tenant_id, f"loop detected: repeated action {hist[-1]!r} ×3")
            return True
        if len(hist) >= 6:
            if hist[-6:] == hist[-6:-3] * 2:
                self._warn(record_id, tenant_id, "cyclical pattern detected")
                return True
        return False

    def _check_stagnation(self, record_id: str, tenant_id: str) -> bool:
        hist = list(self._progress_history[record_id])
        if len(hist) >= 4 and max(hist[-4:]) - min(hist[-4:]) < 0.01:
            self._warn(record_id, tenant_id, "stagnation: progress flat over 4 updates")
            return True
        return False

    def check_deadlock(self, record_id: str, tenant_id: str, waiting_on: str) -> bool:
        rec = self.get(record_id, tenant_id)
        if rec and waiting_on:
            self._warn(record_id, tenant_id, f"potential deadlock: waiting on {waiting_on}")
            return True
        return False

    def predict_failure(self, record_id: str, tenant_id: str) -> dict[str, Any]:
        rec = self.get(record_id, tenant_id)
        if not rec:
            return {"risk": "unknown"}
        warnings = len(rec.warnings)
        risk = "low"
        reasons: list[str] = []
        if warnings >= 3:
            risk = "high"
            reasons.append("multiple warnings")
        if rec.progress < 0.1 and rec.confidence < 0.3:
            risk = "high"
            reasons.append("low progress + low confidence")
        if rec.confidence < 0.2:
            reasons.append("confidence collapse")
            risk = "high"
        return {"risk": risk, "reasons": reasons, "progress": rec.progress, "confidence": rec.confidence}

    def escalate(self, record_id: str, tenant_id: str, action: str = "human_approval") -> SupervisionRecord | None:
        rec = self.get(record_id, tenant_id)
        if not rec:
            return None
        updated = rec.model_copy(update={"escalation": action, "state": "escalated", "updated_at": utc_now()})
        self._records[self._key(tenant_id, record_id)] = updated
        self._publish("agent.supervision.escalated", {"record_id": record_id, "tenant_id": tenant_id, "action": action})
        return updated

    def intervene(self, record_id: str, tenant_id: str, action: str) -> SupervisionRecord | None:
        rec = self.get(record_id, tenant_id)
        if not rec:
            return None
        allowed = {"stop", "pause", "cancel", "strategy_change"}
        if action not in allowed:
            raise ValueError(f"unknown intervention {action!r}")
        updated = rec.model_copy(update={"state": action, "escalation": action, "updated_at": utc_now()})
        self._records[self._key(tenant_id, record_id)] = updated
        self._publish("agent.supervision.warning", {"record_id": record_id, "tenant_id": tenant_id, "action": action})
        return updated

    def switch_strategy(self, record_id: str, tenant_id: str, new_strategy: str, reason: str) -> SupervisionRecord | None:
        rec = self.get(record_id, tenant_id)
        if not rec:
            return None
        updated = rec.model_copy(update={"strategy": new_strategy, "warnings": (*rec.warnings, f"strategy switch: {reason} → {new_strategy}"), "updated_at": utc_now()})
        self._records[self._key(tenant_id, record_id)] = updated
        return updated

    def _warn(self, record_id: str, tenant_id: str, message: str) -> None:
        rec = self.get(record_id, tenant_id)
        if not rec:
            return
        updated = rec.model_copy(update={"warnings": (*rec.warnings, message), "updated_at": utc_now()})
        self._records[self._key(tenant_id, record_id)] = updated
        self._publish("agent.supervision.warning", {"record_id": record_id, "tenant_id": tenant_id, "message": message})

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        try:
            import asyncio
            result = self._event_bus.publish({"type": event_type, **payload})
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)
        except Exception:
            pass
