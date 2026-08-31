"""StrategicFrameworkEngine — manages objectives, initiatives, constraints, state snapshots."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from eaip.shared.time import utc_now
from eaip.strategy.events import (
    ConstraintCreated,
    ConstraintViolated,
    InitiativeCreated,
    InitiativeLinked,
    InitiativeStatusChanged,
    ObjectiveCreated,
    ObjectiveSuperseded,
    ObjectiveUpdated,
    StateChanged,
    StateSnapshotCreated,
)
from eaip.strategy.models import (
    InitiativeStatus,
    ObjectiveStatus,
    StrategicConstraint,
    StrategicInitiative,
    StrategicKPI,
    StrategicMilestone,
    StrategicObjective,
    StrategicRisk,
    StrategicState,
    StrategicTheme,
)
from eaip.strategy.persistence import StrategyStore


class StrategicFrameworkEngine:
    """In-memory strategic framework engine with tenant isolation."""

    def __init__(self, event_bus: Any = None, store: StrategyStore | None = None) -> None:
        self._store = store or StrategyStore()
        self._event_bus = event_bus

    # ── objectives ────────────────────────────────────────────────

    async def create_objective(self, tenant_id: str, title: str, description: str = "", priority: str = "medium", owner: str = "", time_horizon: str = "annual", valid_from: datetime | None = None, valid_until: datetime | None = None) -> StrategicObjective:
        obj_id = f"obj-{uuid.uuid4().hex[:8]}"
        obj = StrategicObjective(
            id=obj_id, tenant_id=tenant_id, title=title, description=description,
            priority=priority, owner=owner, time_horizon=time_horizon,
            valid_from=valid_from, valid_until=valid_until,
        )
        self._store.put_objective(obj)
        await self._publish(ObjectiveCreated(objective_id=obj_id, title=title, priority=priority, tenant_id=tenant_id))
        return obj

    async def update_objective(self, tenant_id: str, objective_id: str, updates: dict[str, Any]) -> StrategicObjective | None:
        obj = self._store.get_objective(tenant_id, objective_id)
        if not obj:
            return None
        updated = obj.model_copy(update=updates)
        self._store.put_objective(updated)
        await self._publish(ObjectiveUpdated(objective_id=objective_id, changes=updates, tenant_id=tenant_id))
        return updated

    async def get_objective(self, tenant_id: str, objective_id: str) -> StrategicObjective | None:
        return self._store.get_objective(tenant_id, objective_id)

    async def list_objectives(self, tenant_id: str, status: str | None = None) -> list[StrategicObjective]:
        objs = self._store.list_objectives(tenant_id)
        if status:
            objs = [o for o in objs if (o.status.value if hasattr(o.status, "value") else str(o.status)) == status]
        return objs

    async def supersede_objective(self, tenant_id: str, old_objective_id: str, new_title: str, new_description: str = "", priority: str = "medium", owner: str = "", time_horizon: str = "annual") -> StrategicObjective | None:
        old = self._store.get_objective(tenant_id, old_objective_id)
        if not old:
            return None
        updated_old = old.model_copy(update={"status": ObjectiveStatus.SUPERSEDED})
        self._store.put_objective(updated_old)
        new_obj = await self.create_objective(tenant_id, new_title, new_description, priority, owner, time_horizon)
        new_obj_with_supersedes = new_obj.model_copy(update={"supersedes": old_objective_id})
        self._store.put_objective(new_obj_with_supersedes)
        await self._publish(ObjectiveSuperseded(old_objective_id=old_objective_id, new_objective_id=new_obj.id, tenant_id=tenant_id))
        return new_obj_with_supersedes

    # ── initiatives ───────────────────────────────────────────────

    async def create_initiative(self, tenant_id: str, objective_id: str, title: str, description: str = "", budget: float = 0.0, owner: str = "") -> StrategicInitiative | None:
        obj = self._store.get_objective(tenant_id, objective_id)
        if not obj:
            return None
        ini_id = f"ini-{uuid.uuid4().hex[:8]}"
        ini = StrategicInitiative(
            id=ini_id, tenant_id=tenant_id, objective_id=objective_id,
            title=title, description=description, budget=budget, owner=owner,
        )
        self._store.put_initiative(ini)
        await self._publish(InitiativeCreated(initiative_id=ini_id, objective_id=objective_id, title=title, tenant_id=tenant_id))
        return ini

    async def link_initiative_to_objective(self, tenant_id: str, initiative_id: str, objective_id: str) -> StrategicInitiative | None:
        ini = self._store.get_initiative(tenant_id, initiative_id)
        if not ini:
            return None
        updated = ini.model_copy(update={"objective_id": objective_id})
        self._store.put_initiative(updated)
        await self._publish(InitiativeLinked(initiative_id=initiative_id, objective_id=objective_id, tenant_id=tenant_id))
        return updated

    async def update_initiative_status(self, tenant_id: str, initiative_id: str, new_status: str) -> StrategicInitiative | None:
        ini = self._store.get_initiative(tenant_id, initiative_id)
        if not ini:
            return None
        old_status = ini.status.value
        updated = ini.model_copy(update={"status": new_status})
        self._store.put_initiative(updated)
        await self._publish(InitiativeStatusChanged(initiative_id=initiative_id, old_status=old_status, new_status=new_status, tenant_id=tenant_id))
        return updated

    async def list_initiatives(self, tenant_id: str, objective_id: str | None = None) -> list[StrategicInitiative]:
        if objective_id:
            return self._store.list_initiatives_for_objective(tenant_id, objective_id)
        return self._store.list_initiatives(tenant_id)

    # ── constraints ───────────────────────────────────────────────

    async def create_constraint(self, tenant_id: str, constraint_type: str, description: str = "", severity: str = "medium", effective_from: datetime | None = None, effective_until: datetime | None = None) -> StrategicConstraint:
        con_id = f"con-{uuid.uuid4().hex[:8]}"
        con = StrategicConstraint(
            id=con_id, tenant_id=tenant_id, type=constraint_type,
            description=description, severity=severity,
            effective_from=effective_from, effective_until=effective_until,
        )
        self._store.put_constraint(con)
        await self._publish(ConstraintCreated(constraint_id=con_id, constraint_type=constraint_type, severity=severity, tenant_id=tenant_id))
        return con

    async def check_constraints(self, tenant_id: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        constraints = self._store.list_constraints(tenant_id)
        now = utc_now()
        violations: list[dict[str, Any]] = []
        for con in constraints:
            if con.effective_from and now < con.effective_from:
                continue
            if con.effective_until and now > con.effective_until:
                continue
            if context and con.type in context:
                violations.append({"constraint_id": con.id, "type": con.type, "severity": con.severity.value, "description": con.description})
                await self._publish(ConstraintViolated(constraint_id=con.id, context=str(context), tenant_id=tenant_id))
        return violations

    # ── themes ────────────────────────────────────────────────────

    async def create_theme(self, tenant_id: str, name: str, description: str = "", weight: float = 1.0) -> StrategicTheme:
        theme_id = f"thm-{uuid.uuid4().hex[:8]}"
        theme = StrategicTheme(id=theme_id, tenant_id=tenant_id, name=name, description=description, weight=weight)
        self._store.put_theme(theme)
        return theme

    async def list_themes(self, tenant_id: str) -> list[StrategicTheme]:
        return self._store.list_themes(tenant_id)

    # ── state snapshots ───────────────────────────────────────────

    async def snapshot_state(self, tenant_id: str, rationale: str = "", approval: str = "") -> StrategicState:
        objectives = self._store.list_objectives(tenant_id)
        snapshot = [o.model_dump(mode="json") for o in objectives]
        latest = self._store.get_latest_state(tenant_id)
        version = (latest.version + 1) if latest else 1
        state_id = f"state-{uuid.uuid4().hex[:8]}"
        state = StrategicState(
            id=state_id, tenant_id=tenant_id, version=version,
            objectives_snapshot=tuple(snapshot), rationale=rationale, approval=approval,
            supersedes=latest.id if latest else None,
        )
        self._store.put_state(state)
        await self._publish(StateSnapshotCreated(state_id=state_id, version=version, tenant_id=tenant_id))
        return state

    async def get_current_state(self, tenant_id: str) -> StrategicState | None:
        return self._store.get_latest_state(tenant_id)

    async def get_state_history(self, tenant_id: str) -> list[StrategicState]:
        return self._store.list_states(tenant_id)

    async def compare_states(self, tenant_id: str, state_id_a: str, state_id_b: str) -> dict[str, Any]:
        a = self._store.get_state(tenant_id, state_id_a)
        b = self._store.get_state(tenant_id, state_id_b)
        if not a or not b:
            return {"error": "one or both states not found"}
        a_ids = {o.get("id") for o in a.objectives_snapshot}
        b_ids = {o.get("id") for o in b.objectives_snapshot}
        added = b_ids - a_ids
        removed = a_ids - b_ids
        common = a_ids & b_ids
        changes: list[dict[str, Any]] = []
        a_map = {o.get("id"): o for o in a.objectives_snapshot}
        b_map = {o.get("id"): o for o in b.objectives_snapshot}
        for oid in common:
            if a_map[oid] != b_map[oid]:
                changes.append({"objective_id": oid, "before": a_map[oid], "after": b_map[oid]})
        return {
            "state_a": state_id_a, "state_b": state_id_b,
            "added": list(added), "removed": list(removed),
            "changed": changes, "version_a": a.version, "version_b": b.version,
        }

    # ── milestones ────────────────────────────────────────────────

    async def create_milestone(self, tenant_id: str, initiative_id: str, title: str, target_date: datetime | None = None, owner: str = "") -> StrategicMilestone:
        ms_id = f"ms-{uuid.uuid4().hex[:8]}"
        ms = StrategicMilestone(id=ms_id, tenant_id=tenant_id, initiative_id=initiative_id, title=title, target_date=target_date, owner=owner)
        self._store.put_milestone(ms)
        return ms

    async def list_milestones(self, tenant_id: str, initiative_id: str = "") -> list[StrategicMilestone]:
        return self._store.list_milestones(tenant_id, initiative_id)

    # ── risks ─────────────────────────────────────────────────────

    async def create_risk(self, tenant_id: str, objective_id: str, description: str = "", likelihood: str = "medium", impact: str = "medium", mitigation: str = "") -> StrategicRisk:
        risk_id = f"risk-{uuid.uuid4().hex[:8]}"
        risk = StrategicRisk(
            id=risk_id, tenant_id=tenant_id, objective_id=objective_id,
            description=description, likelihood=likelihood, impact=impact, mitigation=mitigation,
        )
        self._store.put_risk(risk)
        return risk

    async def list_risks(self, tenant_id: str, objective_id: str = "") -> list[StrategicRisk]:
        return self._store.list_risks(tenant_id, objective_id)

    # ── kpis ──────────────────────────────────────────────────────

    async def create_kpi(self, tenant_id: str, objective_id: str, name: str, target: float = 0.0, current: float = 0.0, trend: str = "stable") -> StrategicKPI:
        kpi_id = f"kpi-{uuid.uuid4().hex[:8]}"
        kpi = StrategicKPI(id=kpi_id, tenant_id=tenant_id, objective_id=objective_id, name=name, target=target, current=current, trend=trend)
        self._store.put_kpi(kpi)
        return kpi

    async def list_kpis(self, tenant_id: str, objective_id: str = "") -> list[StrategicKPI]:
        return self._store.list_kpis(tenant_id, objective_id)

    # ── internal ──────────────────────────────────────────────────

    async def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            try:
                import asyncio
                result = self._event_bus.publish(event)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception:
                pass


__all__ = ["StrategicFrameworkEngine"]
