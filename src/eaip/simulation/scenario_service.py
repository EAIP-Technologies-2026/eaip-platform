"""ScenarioEngine — baseline / alternative / counterfactual simulation.

Tenant-isolated. Each scenario belongs to exactly one tenant.
Deterministic: all outcomes derived from stable hashing of inputs.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


def _stable_float(seed: str, low: float = 0.0, high: float = 1.0) -> float:
    h = hashlib.sha256(seed.encode()).hexdigest()
    # use first 8 hex chars -> 32-bit int
    n = int(h[:8], 16)
    frac = n / 0xFFFFFFFF
    return round(low + frac * (high - low), 3)


def _confidence_for(intervention: dict[str, Any], constraints: dict[str, Any]) -> float:
    # More constraints -> lower confidence; empty -> higher
    base = 0.78
    if constraints:
        base -= min(0.25, len(constraints) * 0.04)
    if intervention.get("risk") == "high":
        base -= 0.15
    return round(max(0.35, min(0.95, base)), 2)


class Alternative(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    alt_id: str
    intervention: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class Scenario(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    scenario_id: str
    tenant_id: str
    name: str
    baseline_state: dict[str, Any] = Field(default_factory=dict)
    alternatives: tuple[Alternative, ...] = Field(default_factory=tuple)
    steps: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class ScenarioEngine:
    """Tenant-isolated scenario / counterfactual engine.

    Does not duplicate SimulationEngine; operates at the scenario-
    planning level and delegates event-level simulation to the
    SimulationEngine only if one is injected.
    """

    def __init__(self, simulation_engine: Any | None = None) -> None:
        self._simulation = simulation_engine
        self._store: dict[str, Scenario] = {}  # key = f"{tenant_id}:{scenario_id}"

    def _key(self, tenant_id: str, scenario_id: str) -> str:
        return f"{tenant_id}:{scenario_id}"

    # ── CRUD ──────────────────────────────────────────────────────

    def create_scenario(self, tenant: str, baseline_state: dict[str, Any], name: str) -> str:
        scenario_id = f"scn-{uuid.uuid4().hex[:8]}"
        baseline = dict(baseline_state) if baseline_state else {}
        # initial replay steps derived from baseline
        steps: list[dict[str, Any]] = [
            {"step": 0, "phase": "baseline", "state": baseline, "at": utc_now().isoformat()},
        ]
        scn = Scenario(
            scenario_id=scenario_id,
            tenant_id=tenant,
            name=name,
            baseline_state=baseline,
            alternatives=(),
            steps=tuple(steps),
        )
        self._store[self._key(tenant, scenario_id)] = scn
        return scenario_id

    def get(self, scenario_id: str, tenant: str) -> Scenario | None:
        return self._store.get(self._key(tenant, scenario_id))

    def add_alternative(
        self,
        scenario_id: str,
        tenant: str,
        intervention: dict[str, Any],
        constraints: dict[str, Any],
    ) -> str:
        scn = self.get(scenario_id, tenant)
        if scn is None:
            raise KeyError(f"scenario {scenario_id!r} not found for tenant {tenant!r}")
        alt_id = f"alt-{uuid.uuid4().hex[:8]}"
        alt = Alternative(
            alt_id=alt_id,
            intervention=dict(intervention) if intervention else {},
            constraints=dict(constraints) if constraints else {},
        )
        new_steps = list(scn.steps) + [
            {
                "step": len(scn.steps),
                "phase": "alternative",
                "alt_id": alt_id,
                "intervention": alt.intervention,
                "constraints": alt.constraints,
                "at": utc_now().isoformat(),
            }
        ]
        updated = scn.model_copy(update={"alternatives": (*scn.alternatives, alt), "steps": tuple(new_steps)})
        self._store[self._key(tenant, scenario_id)] = updated
        return alt_id

    # ── counterfactual ────────────────────────────────────────────

    def run_counterfactual(self, scenario_id: str, tenant: str, question: str) -> dict[str, Any]:
        scn = self.get(scenario_id, tenant)
        if scn is None:
            raise KeyError(f"scenario {scenario_id!r} not found for tenant {tenant!r}")
        q = question.strip() if question else "what-if baseline"
        # deterministic derived values
        seed = f"{tenant}:{scenario_id}:{q}"
        fact = scn.baseline_state
        assumption = {"question": q, "baseline_keys": sorted(fact.keys())}
        outcome_seed = f"{seed}:{sorted(fact.items())}"
        cost = int(_stable_float(outcome_seed + ":cost", 5_000, 150_000))
        time_days = int(_stable_float(outcome_seed + ":time", 2, 45))
        risk = _stable_float(outcome_seed + ":risk", 0.1, 0.9)
        confidence = _confidence_for({"question": q}, {})
        # adjust confidence based on question length deterministically
        confidence = round(max(0.35, min(0.95, confidence - (len(q) % 5) * 0.02)), 2)
        simulated_outcome = {
            "cost": cost,
            "time_days": time_days,
            "risk": risk,
            "capacity_delta": _stable_float(outcome_seed + ":cap", -0.3, 0.4),
            "outcome": f"simulated outcome for '{q}'",
        }
        return {
            "fact": fact,
            "assumption": assumption,
            "simulated_outcome": simulated_outcome,
            "confidence": confidence,
        }

    # ── compare ───────────────────────────────────────────────────

    def compare(self, scenario_ids: list[str], tenant: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for sid in scenario_ids:
            scn = self.get(sid, tenant)
            if scn is None:
                result[sid] = {"error": "not found or not owned by tenant"}
                continue
            baseline = scn.baseline_state
            # deterministic per-scenario metrics
            seed = f"{tenant}:{sid}:{sorted(baseline.items())}"
            # include alternatives influence
            alt_count = len(scn.alternatives)
            cost = int(_stable_float(seed + ":cost", 10_000, 200_000) * (1 + alt_count * 0.07))
            time_v = int(_stable_float(seed + ":time", 5, 60) * (1 + alt_count * 0.05))
            risk = _stable_float(seed + ":risk", 0.15, 0.85)
            capacity = _stable_float(seed + ":capacity", 0.4, 0.95)
            outcome = f"projected outcome for {scn.name} with {alt_count} alternative(s)"
            confidence = _confidence_for({"alts": alt_count}, {"scenarios": len(scenario_ids)})
            result[sid] = {
                "cost": cost,
                "time": time_v,
                "risk": risk,
                "capacity": capacity,
                "outcome": outcome,
                "confidence": confidence,
            }
        return result

    # ── replay ────────────────────────────────────────────────────

    def replay(self, scenario_id: str, tenant: str) -> list[dict[str, Any]]:
        scn = self.get(scenario_id, tenant)
        if scn is None:
            raise KeyError(f"scenario {scenario_id!r} not found for tenant {tenant!r}")
        return [dict(s) for s in scn.steps]

    def branch(self, scenario_id: str, tenant: str, name: str) -> str:
        scn = self.get(scenario_id, tenant)
        if scn is None:
            raise KeyError(f"scenario {scenario_id!r} not found")
        new_id = f"scn-{uuid.uuid4().hex[:8]}"
        new_scn = Scenario(scenario_id=new_id, tenant_id=tenant, name=name or f"{scn.name} (branch)", baseline_state=dict(scn.baseline_state), alternatives=scn.alternatives, steps=tuple(list(scn.steps) + [{"step": len(scn.steps), "phase": "branch", "from": scenario_id, "at": utc_now().isoformat()}]))
        self._store[self._key(tenant, new_id)] = new_scn
        return new_id

    def monte_carlo(self, scenario_id: str, tenant: str, runs: int = 10) -> dict[str, Any]:
        scn = self.get(scenario_id, tenant)
        if scn is None:
            raise KeyError(f"scenario {scenario_id!r} not found")
        runs = max(1, min(50, runs))
        costs: list[int] = []
        risks: list[float] = []
        for i in range(runs):
            cf = self.run_counterfactual(scenario_id, tenant, f"mc-run-{i}")
            costs.append(int(cf["simulated_outcome"]["cost"]))
            risks.append(float(cf["simulated_outcome"]["risk"]))
        costs_sorted = sorted(costs)
        return {"scenario_id": scenario_id, "runs": runs, "cost": {"min": costs_sorted[0], "max": costs_sorted[-1], "median": costs_sorted[len(costs_sorted)//2], "mean": int(sum(costs)/len(costs))}, "risk": {"min": min(risks), "max": max(risks), "mean": round(sum(risks)/len(risks), 3)}, "confidence_range": [round(min(risks),2), round(max(risks),2)]}

    def sensitivity(self, scenario_id: str, tenant: str, param: str = "cost") -> dict[str, Any]:
        scn = self.get(scenario_id, tenant)
        if scn is None:
            raise KeyError(f"scenario {scenario_id!r} not found")
        base = self.run_counterfactual(scenario_id, tenant, f"sensitivity:{param}")
        base_val = base["simulated_outcome"].get(param, 0)
        return {"scenario_id": scenario_id, "param": param, "baseline": base_val, "delta_pct": 10, "sensitivity": round(float(base_val) * 0.1, 2)}

    def list_for_tenant(self, tenant: str) -> list[Scenario]:
        prefix = f"{tenant}:"
        return [v for k, v in self._store.items() if k.startswith(prefix)]


__all__ = ["Alternative", "Scenario", "ScenarioEngine"]
