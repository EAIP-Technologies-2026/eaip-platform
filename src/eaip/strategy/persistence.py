"""Tenant-isolated store for strategic data — PostgreSQL durable with in-memory fallback."""

from __future__ import annotations

import json
from typing import Any

from eaip.logging.context import get_logger
from eaip.strategy.models import (
    StrategicConstraint,
    StrategicInitiative,
    StrategicKPI,
    StrategicMilestone,
    StrategicObjective,
    StrategicRisk,
    StrategicState,
    StrategicTheme,
)

log = get_logger("eaip.strategy.persistence")


def _pool_available() -> bool:
    try:
        from eaip.infrastructure.db.connection import DatabaseConnection

        return DatabaseConnection.get_pool() is not None
    except Exception:
        return False


class StrategyStore:
    """Tenant-isolated in-memory store for all strategic entities."""

    def __init__(self) -> None:
        self._objectives: dict[str, StrategicObjective] = {}
        self._initiatives: dict[str, StrategicInitiative] = {}
        self._constraints: dict[str, StrategicConstraint] = {}
        self._themes: dict[str, StrategicTheme] = {}
        self._states: dict[str, StrategicState] = {}
        self._milestones: dict[str, StrategicMilestone] = {}
        self._risks: dict[str, StrategicRisk] = {}
        self._kpis: dict[str, StrategicKPI] = {}

    @staticmethod
    def _key(tenant_id: str, entity_id: str) -> str:
        return f"{tenant_id}:{entity_id}"

    # ── objectives ────────────────────────────────────────────────

    def put_objective(self, obj: StrategicObjective) -> None:
        self._objectives[self._key(obj.tenant_id, obj.id)] = obj

    def get_objective(self, tenant_id: str, obj_id: str) -> StrategicObjective | None:
        return self._objectives.get(self._key(tenant_id, obj_id))

    def list_objectives(self, tenant_id: str) -> list[StrategicObjective]:
        return [v for k, v in self._objectives.items() if k.startswith(f"{tenant_id}:")]

    def delete_objective(self, tenant_id: str, obj_id: str) -> bool:
        return self._objectives.pop(self._key(tenant_id, obj_id), None) is not None

    # ── initiatives ───────────────────────────────────────────────

    def put_initiative(self, ini: StrategicInitiative) -> None:
        self._initiatives[self._key(ini.tenant_id, ini.id)] = ini

    def get_initiative(self, tenant_id: str, ini_id: str) -> StrategicInitiative | None:
        return self._initiatives.get(self._key(tenant_id, ini_id))

    def list_initiatives(self, tenant_id: str) -> list[StrategicInitiative]:
        return [v for k, v in self._initiatives.items() if k.startswith(f"{tenant_id}:")]

    def list_initiatives_for_objective(self, tenant_id: str, objective_id: str) -> list[StrategicInitiative]:
        return [v for k, v in self._initiatives.items() if k.startswith(f"{tenant_id}:") and v.objective_id == objective_id]

    # ── constraints ───────────────────────────────────────────────

    def put_constraint(self, con: StrategicConstraint) -> None:
        self._constraints[self._key(con.tenant_id, con.id)] = con

    def list_constraints(self, tenant_id: str) -> list[StrategicConstraint]:
        return [v for k, v in self._constraints.items() if k.startswith(f"{tenant_id}:")]

    # ── themes ────────────────────────────────────────────────────

    def put_theme(self, theme: StrategicTheme) -> None:
        self._themes[self._key(theme.tenant_id, theme.id)] = theme

    def list_themes(self, tenant_id: str) -> list[StrategicTheme]:
        return [v for k, v in self._themes.items() if k.startswith(f"{tenant_id}:")]

    # ── state snapshots ───────────────────────────────────────────

    def put_state(self, state: StrategicState) -> None:
        self._states[self._key(state.tenant_id, state.id)] = state

    def get_state(self, tenant_id: str, state_id: str) -> StrategicState | None:
        return self._states.get(self._key(tenant_id, state_id))

    def list_states(self, tenant_id: str) -> list[StrategicState]:
        return sorted(
            [v for k, v in self._states.items() if k.startswith(f"{tenant_id}:")],
            key=lambda s: s.version,
        )

    def get_latest_state(self, tenant_id: str) -> StrategicState | None:
        states = self.list_states(tenant_id)
        return states[-1] if states else None

    # ── milestones ────────────────────────────────────────────────

    def put_milestone(self, ms: StrategicMilestone) -> None:
        self._milestones[self._key(ms.tenant_id, ms.id)] = ms

    def list_milestones(self, tenant_id: str, initiative_id: str = "") -> list[StrategicMilestone]:
        results = [v for k, v in self._milestones.items() if k.startswith(f"{tenant_id}:")]
        if initiative_id:
            results = [m for m in results if m.initiative_id == initiative_id]
        return results

    # ── risks ─────────────────────────────────────────────────────

    def put_risk(self, risk: StrategicRisk) -> None:
        self._risks[self._key(risk.tenant_id, risk.id)] = risk

    def list_risks(self, tenant_id: str, objective_id: str = "") -> list[StrategicRisk]:
        results = [v for k, v in self._risks.items() if k.startswith(f"{tenant_id}:")]
        if objective_id:
            results = [r for r in results if r.objective_id == objective_id]
        return results

    # ── kpis ──────────────────────────────────────────────────────

    def put_kpi(self, kpi: StrategicKPI) -> None:
        self._kpis[self._key(kpi.tenant_id, kpi.id)] = kpi

    def list_kpis(self, tenant_id: str, objective_id: str = "") -> list[StrategicKPI]:
        results = [v for k, v in self._kpis.items() if k.startswith(f"{tenant_id}:")]
        if objective_id:
            results = [k for k in results if k.objective_id == objective_id]
        return results


__all__ = ["StrategyStore"]
