from __future__ import annotations

import asyncio
import uuid
from typing import Any

from eaip.logging.context import get_logger
from eaip.long_missions.models import LongMissionRecord, LongMissionStatus, MissionCheckpoint
from eaip.shared.time import utc_now

log = get_logger("eaip.long_missions.service")

APPROVAL_REQUIRED_ACTIONS = {"financial_change", "external_write", "destructive", "customer_comm", "production_change"}


class LongMissionService:
    def __init__(self, event_bus: Any | None = None) -> None:
        self._missions: dict[str, LongMissionRecord] = {}
        self._event_bus = event_bus

    def _key(self, tenant_id: str, mission_id: str) -> str:
        return f"{tenant_id}:{mission_id}"

    def create(self, mission_id: str, tenant_id: str, name: str, steps: list[dict[str, Any]] | None = None, autonomy_level: str = "SUGGEST", metadata: dict[str, Any] | None = None) -> LongMissionRecord:
        rec = LongMissionRecord(mission_id=mission_id, tenant_id=tenant_id, name=name, steps=tuple(steps or []), autonomy_level=autonomy_level, metadata=metadata or {})
        self._missions[self._key(tenant_id, mission_id)] = rec
        return rec

    def get(self, mission_id: str, tenant_id: str) -> LongMissionRecord | None:
        return self._missions.get(self._key(tenant_id, mission_id))

    def list_for_tenant(self, tenant_id: str) -> list[LongMissionRecord]:
        return [v for k, v in self._missions.items() if k.startswith(f"{tenant_id}:")]

    def checkpoint(self, mission_id: str, tenant_id: str, state: dict[str, Any] | None = None) -> MissionCheckpoint | None:
        rec = self.get(mission_id, tenant_id)
        if not rec:
            return None
        cp = MissionCheckpoint(checkpoint_id=f"ckpt-{uuid.uuid4().hex[:8]}", mission_id=mission_id, tenant_id=tenant_id, step_index=rec.current_step, state=state or {"step": rec.current_step, "durable": True, "idempotency_key": f"mission:{mission_id}:step:{rec.current_step}"})
        updated = rec.model_copy(update={"checkpoints": (*rec.checkpoints, cp), "status": LongMissionStatus.checkpointed, "updated_at": utc_now()})
        self._missions[self._key(tenant_id, mission_id)] = updated
        self._publish("mission.checkpointed", {"mission_id": mission_id, "tenant_id": tenant_id, "checkpoint_id": cp.checkpoint_id})
        return cp

    def recover(self, mission_id: str, tenant_id: str) -> LongMissionRecord | None:
        rec = self.get(mission_id, tenant_id)
        if not rec:
            return None
        if not rec.checkpoints:
            return self.resume(mission_id, tenant_id)
        last = rec.checkpoints[-1]
        # never duplicate irreversible step — resume from checkpoint
        updated = rec.model_copy(update={"current_step": last.step_index, "status": LongMissionStatus.running, "updated_at": utc_now()})
        self._missions[self._key(tenant_id, mission_id)] = updated
        self._publish("mission.recovered", {"mission_id": mission_id, "tenant_id": tenant_id, "checkpoint_id": last.checkpoint_id})
        return updated

    def escalate(self, mission_id: str, tenant_id: str, reason: str = "") -> LongMissionRecord | None:
        rec = self.get(mission_id, tenant_id)
        if not rec:
            return None
        updated = rec.model_copy(update={"status": LongMissionStatus.failed, "updated_at": utc_now(), "metadata": {**rec.metadata, "escalation_reason": reason}})
        self._missions[self._key(tenant_id, mission_id)] = updated
        self._publish("mission.escalated", {"mission_id": mission_id, "tenant_id": tenant_id, "reason": reason})
        return updated

    def resume(self, mission_id: str, tenant_id: str) -> LongMissionRecord | None:
        rec = self.get(mission_id, tenant_id)
        if not rec:
            return None
        updated = rec.model_copy(update={"status": LongMissionStatus.running, "updated_at": utc_now()})
        self._missions[self._key(tenant_id, mission_id)] = updated
        return updated

    def pause(self, mission_id: str, tenant_id: str) -> LongMissionRecord | None:
        rec = self.get(mission_id, tenant_id)
        if not rec:
            return None
        updated = rec.model_copy(update={"status": LongMissionStatus.paused, "updated_at": utc_now()})
        self._missions[self._key(tenant_id, mission_id)] = updated
        return updated

    def cancel(self, mission_id: str, tenant_id: str) -> LongMissionRecord | None:
        rec = self.get(mission_id, tenant_id)
        if not rec:
            return None
        updated = rec.model_copy(update={"status": LongMissionStatus.cancelled, "updated_at": utc_now()})
        self._missions[self._key(tenant_id, mission_id)] = updated
        return updated

    def advance(self, mission_id: str, tenant_id: str) -> LongMissionRecord | None:
        rec = self.get(mission_id, tenant_id)
        if not rec:
            return None
        if rec.current_step >= len(rec.steps) - 1:
            updated = rec.model_copy(update={"status": LongMissionStatus.completed, "updated_at": utc_now()})
        else:
            updated = rec.model_copy(update={"current_step": rec.current_step + 1, "status": LongMissionStatus.running, "updated_at": utc_now()})
        self._missions[self._key(tenant_id, mission_id)] = updated
        return updated

    def propose_workflow(self, mission_id: str, tenant_id: str, workflow_spec: dict[str, Any]) -> dict[str, Any]:
        rec = self.get(mission_id, tenant_id)
        if not rec:
            raise ValueError("mission not found")
        requires_approval = any(a in str(workflow_spec) for a in APPROVAL_REQUIRED_ACTIONS) or workflow_spec.get("requires_approval")
        return {"mission_id": mission_id, "workflow_spec": workflow_spec, "requires_approval": bool(requires_approval), "status": "pending_approval" if requires_approval else "approved"}

    def check_autonomy(self, mission_id: str, tenant_id: str, action: str) -> bool:
        rec = self.get(mission_id, tenant_id)
        if not rec:
            return False
        level = rec.autonomy_level
        risky = action in APPROVAL_REQUIRED_ACTIONS
        if risky and level in ("READ_ONLY", "SUGGEST", "APPROVAL_REQUIRED"):
            return False
        return True

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        try:
            result = self._event_bus.publish({"type": event_type, **payload})
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)
        except Exception:
            pass

    def __init_subclass__(cls) -> None:
        pass
