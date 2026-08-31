from __future__ import annotations

import asyncio
import uuid
from typing import Any

from eaip.logging.context import get_logger
from eaip.onboarding.models import OnboardingSession, OnboardingStatus
from eaip.shared.time import utc_now

log = get_logger("eaip.onboarding.service")

STEPS = ["company", "industry", "pack", "resources", "simulation", "dashboard"]


class OnboardingService:
    def __init__(self, solution_registry: Any | None = None, event_bus: Any | None = None) -> None:
        self._registry = solution_registry
        self._event_bus = event_bus
        self._sessions: dict[str, OnboardingSession] = {}

    def create(self, tenant_id: str, company_name: str, industry: str = "", pack_id: str = "", metadata: dict[str, Any] | None = None) -> OnboardingSession:
        session_id = f"ob-{uuid.uuid4().hex[:8]}"
        sess = OnboardingSession(session_id=session_id, tenant_id=tenant_id, company_name=company_name, industry=industry, pack_id=pack_id, status=OnboardingStatus.pending, progress=0, steps=tuple(STEPS), current_step=STEPS[0], metadata=metadata or {})
        self._sessions[session_id] = sess
        return sess

    def get(self, session_id: str, tenant_id: str) -> OnboardingSession | None:
        sess = self._sessions.get(session_id)
        if sess and sess.tenant_id == tenant_id:
            return sess
        return None

    def list_for_tenant(self, tenant_id: str) -> list[OnboardingSession]:
        return [v for v in self._sessions.values() if v.tenant_id == tenant_id]

    async def advance(self, session_id: str, tenant_id: str, step_data: dict[str, Any] | None = None) -> OnboardingSession | None:
        sess = self.get(session_id, tenant_id)
        if not sess:
            return None
        step_data = step_data or {}
        idx = STEPS.index(sess.current_step) if sess.current_step in STEPS else -1
        next_idx = idx + 1
        if "industry" in step_data:
            sess = sess.model_copy(update={"industry": str(step_data["industry"])})
        if "pack_id" in step_data or "packId" in step_data:
            pid = str(step_data.get("pack_id") or step_data.get("packId") or "")
            sess = sess.model_copy(update={"pack_id": pid})
            if self._registry and pid:
                try:
                    self._registry.install(pid, tenant_id, config=step_data)
                except Exception as exc:
                    log.warning("onboarding.pack_install_failed", error=str(exc))
        if next_idx >= len(STEPS):
            sess = sess.model_copy(update={"status": OnboardingStatus.completed, "progress": 100, "current_step": STEPS[-1], "updated_at": utc_now()})
        else:
            progress = int((next_idx + 1) / len(STEPS) * 100)
            status = OnboardingStatus.in_progress if progress < 100 else OnboardingStatus.completed
            sess = sess.model_copy(update={"status": status, "progress": progress, "current_step": STEPS[next_idx], "updated_at": utc_now()})
        self._sessions[session_id] = sess
        self._publish("onboarding.advanced", {"session_id": session_id, "tenant_id": tenant_id, "step": sess.current_step})
        return sess

    def update(self, session_id: str, tenant_id: str, patch: dict[str, Any]) -> OnboardingSession | None:
        sess = self.get(session_id, tenant_id)
        if not sess:
            return None
        merged = sess.model_dump()
        merged.update(patch)
        merged["updated_at"] = utc_now()
        updated = OnboardingSession.model_validate(merged)
        self._sessions[session_id] = updated
        return updated

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        try:
            result = self._event_bus.publish({"type": event_type, **payload})
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)
        except Exception:
            pass
