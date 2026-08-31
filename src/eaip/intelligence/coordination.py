from __future__ import annotations

import uuid
from typing import Any

from eaip.intelligence.models import CoordinationPlan
from eaip.shared.time import utc_now


class CoordinationEngine:
    def __init__(self, workforce_analytics: Any | None = None, scheduling_service: Any | None = None, swarm_engine: Any | None = None, event_bus: Any | None = None) -> None:
        self._workforce = workforce_analytics
        self._scheduling = scheduling_service
        self._swarm = swarm_engine
        self._event_bus = event_bus
        self._plans: dict[str, CoordinationPlan] = {}

    def _key(self, tenant_id: str, plan_id: str) -> str:
        return f"{tenant_id}:{plan_id}"

    def create_plan(self, tenant_id: str, objective: str, priority: str = "operational", tasks: list[dict[str, Any]] | None = None) -> CoordinationPlan:
        plan_id = f"coord-{uuid.uuid4().hex[:8]}"
        plan = CoordinationPlan(plan_id=plan_id, tenant_id=tenant_id, objective=objective, priority=priority, tasks=tuple(tasks or []))
        self._plans[self._key(tenant_id, plan_id)] = plan
        self._publish("coordination.started", {"plan_id": plan_id, "tenant_id": tenant_id, "objective": objective})
        return plan

    def get(self, plan_id: str, tenant_id: str) -> CoordinationPlan | None:
        return self._plans.get(self._key(tenant_id, plan_id))

    def list_for_tenant(self, tenant_id: str) -> list[CoordinationPlan]:
        return [v for k, v in self._plans.items() if k.startswith(f"{tenant_id}:")]

    def delegate(self, plan_id: str, tenant_id: str, capabilities: list[str] | None = None) -> CoordinationPlan | None:
        plan = self.get(plan_id, tenant_id)
        if not plan:
            return None
        agents = tuple(capabilities or ["agent-1", "agent-2"])
        updated = plan.model_copy(update={"assigned_agents": agents, "status": "delegated"})
        self._plans[self._key(tenant_id, plan_id)] = updated
        return updated

    def allocate_resources(self, plan_id: str, tenant_id: str, resources: dict[str, Any]) -> CoordinationPlan | None:
        plan = self.get(plan_id, tenant_id)
        if not plan:
            return None
        updated = plan.model_copy(update={"resources": resources, "status": "resourced"})
        self._plans[self._key(tenant_id, plan_id)] = updated
        return updated

    def detect_conflicts(self, plan_id: str, tenant_id: str) -> list[dict[str, Any]]:
        plan = self.get(plan_id, tenant_id)
        if not plan:
            return []
        conflicts: list[dict[str, Any]] = []
        if len(plan.assigned_agents) > 5:
            conflicts.append({"type": "resource", "description": "too many agents", "severity": "medium"})
        if plan.priority == "urgent" and plan.status != "delegated":
            conflicts.append({"type": "priority", "description": "urgent plan not yet delegated", "severity": "high"})
        if conflicts:
            updated = plan.model_copy(update={"conflicts": tuple(conflicts)})
            self._plans[self._key(tenant_id, plan_id)] = updated
            self._publish("coordination.conflict.detected", {"plan_id": plan_id, "tenant_id": tenant_id, "conflicts": conflicts})
        return conflicts

    def adapt(self, plan_id: str, tenant_id: str, reason: str, new_tasks: list[dict[str, Any]] | None = None) -> CoordinationPlan | None:
        plan = self.get(plan_id, tenant_id)
        if not plan:
            return None
        tasks = tuple(new_tasks) if new_tasks is not None else plan.tasks
        updated = plan.model_copy(update={"tasks": tasks, "status": "adapted", "outcome": f"adapted: {reason}"})
        self._plans[self._key(tenant_id, plan_id)] = updated
        return updated

    def verify_outcome(self, plan_id: str, tenant_id: str, outcome: str, success: bool) -> CoordinationPlan | None:
        plan = self.get(plan_id, tenant_id)
        if not plan:
            return None
        status = "completed" if success else "failed"
        updated = plan.model_copy(update={"outcome": outcome, "status": status})
        self._plans[self._key(tenant_id, plan_id)] = updated
        if success:
            self._publish("coordination.completed", {"plan_id": plan_id, "tenant_id": tenant_id, "outcome": outcome})
        return updated

    def intervene(self, plan_id: str, tenant_id: str, action: str) -> CoordinationPlan | None:
        plan = self.get(plan_id, tenant_id)
        if not plan:
            return None
        updated = plan.model_copy(update={"status": action})
        self._plans[self._key(tenant_id, plan_id)] = updated
        return updated

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
