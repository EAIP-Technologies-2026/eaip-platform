"""Recursive Intelligence Loop (RIL) — observe → reason → plan → execute → measure → reflect → correct."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class IntelligenceCycle(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")

    id: str
    tenant_id: str
    objective: str
    context: dict[str, Any] = Field(default_factory=dict)
    observations: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    reasoning: dict[str, Any] = Field(default_factory=dict)
    plan: dict[str, Any] = Field(default_factory=dict)
    actions: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    measurements: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    reflection: dict[str, Any] = Field(default_factory=dict)
    correction: dict[str, Any] = Field(default_factory=dict)
    resulting_state: dict[str, Any] = Field(default_factory=dict)
    status: str = "started"
    autonomy_level: str = "L2"


class RecursiveIntelligenceEngine:
    """Drives recursive intelligence cycles with autonomy enforcement."""

    def __init__(
        self,
        cognitive_engine: Any | None = None,
        coordination_engine: Any | None = None,
        kpi_engine: Any | None = None,
        autonomy_engine: Any | None = None,
        policy_engine: Any | None = None,
        event_bus: Any | None = None,
    ) -> None:
        self._cognitive = cognitive_engine
        self._coordination = coordination_engine
        self._kpi = kpi_engine
        self._autonomy = autonomy_engine
        self._policy = policy_engine
        self._event_bus = event_bus
        self._cycles: dict[str, IntelligenceCycle] = {}

    def _key(self, tenant_id: str, cycle_id: str) -> str:
        return f"{tenant_id}:{cycle_id}"

    async def start_cycle(self, tenant_id: str, objective: str, context: dict[str, Any] | None = None, autonomy_level: str = "L2") -> IntelligenceCycle:
        cycle_id = f"ril-{uuid.uuid4().hex[:8]}"
        cycle = IntelligenceCycle(id=cycle_id, tenant_id=tenant_id, objective=objective, context=context or {}, autonomy_level=autonomy_level)
        self._cycles[self._key(tenant_id, cycle_id)] = cycle
        self._publish("ril.cycle.started", {"cycle_id": cycle_id, "tenant_id": tenant_id, "objective": objective})
        return cycle

    async def observe(self, cycle_id: str, tenant_id: str, observations: list[dict[str, Any]]) -> IntelligenceCycle | None:
        cycle = self._get(cycle_id, tenant_id)
        if not cycle:
            return None
        cycle.observations = tuple(observations)
        cycle.status = "observed"
        self._publish("ril.cycle.observed", {"cycle_id": cycle_id, "tenant_id": tenant_id})
        return cycle

    async def reason(self, cycle_id: str, tenant_id: str) -> dict[str, Any]:
        cycle = self._get(cycle_id, tenant_id)
        if not cycle:
            return {"error": "cycle not found"}
        if self._cognitive:
            try:
                hyp = await self._cognitive.reason(tenant_id, cycle.objective, strategy="evidence_first")
                cycle.reasoning = {"hypothesis_id": hyp.hypothesis_id, "title": hyp.title, "confidence": hyp.confidence, "evidence_count": len(hyp.evidence), "strategy": hyp.reasoning_strategy}
            except Exception:
                cycle.reasoning = {"fallback": True, "objective": cycle.objective}
        else:
            cycle.reasoning = {"direct": True, "objective": cycle.objective, "observations": len(cycle.observations)}
        cycle.status = "reasoned"
        self._publish("ril.cycle.reasoned", {"cycle_id": cycle_id, "tenant_id": tenant_id})
        return cycle.reasoning

    async def plan(self, cycle_id: str, tenant_id: str) -> dict[str, Any]:
        cycle = self._get(cycle_id, tenant_id)
        if not cycle:
            return {"error": "cycle not found"}
        if self._coordination:
            try:
                coord_plan = self._coordination.create_plan(tenant_id, cycle.objective, priority="strategic")
                cycle.plan = {"plan_id": coord_plan.plan_id, "objective": coord_plan.objective, "priority": coord_plan.priority}
            except Exception:
                cycle.plan = {"fallback": True, "objective": cycle.objective}
        else:
            cycle.plan = {"direct": True, "objective": cycle.objective, "reasoning": cycle.reasoning}
        cycle.status = "planned"
        self._publish("ril.cycle.planned", {"cycle_id": cycle_id, "tenant_id": tenant_id})
        return cycle.plan

    async def execute(self, cycle_id: str, tenant_id: str) -> dict[str, Any]:
        cycle = self._get(cycle_id, tenant_id)
        if not cycle:
            return {"error": "cycle not found"}
        autonomy_check = self._check_autonomy(tenant_id, "ril.execute", cycle.autonomy_level)
        if autonomy_check.get("decision") == "DENY":
            cycle.status = "blocked"
            return {"error": "autonomy denied", "reason": autonomy_check.get("reason")}
        if autonomy_check.get("decision") == "REQUIRE_APPROVAL":
            cycle.status = "pending_approval"
            return {"status": "pending_approval", "reason": autonomy_check.get("reason")}
        action = {"type": "execute", "plan": cycle.plan, "autonomy": autonomy_check}
        cycle.actions = (action,)
        cycle.status = "executed"
        self._publish("ril.cycle.executed", {"cycle_id": cycle_id, "tenant_id": tenant_id})
        return {"status": "executed", "actions": len(cycle.actions)}

    async def measure(self, cycle_id: str, tenant_id: str) -> list[dict[str, Any]]:
        cycle = self._get(cycle_id, tenant_id)
        if not cycle:
            return [{"error": "cycle not found"}]
        measurements: list[dict[str, Any]] = []
        if self._kpi:
            try:
                kpis = await self._kpi.list_kpis()
                for kpi in kpis[:5]:
                    eval_result = await self._kpi.evaluate_kpi(kpi.id)
                    measurements.append(eval_result)
            except Exception:
                measurements.append({"source": "fallback", "count": len(cycle.actions)})
        else:
            measurements.append({"source": "direct", "actions_measured": len(cycle.actions)})
        cycle.measurements = tuple(measurements)
        cycle.status = "measured"
        self._publish("ril.cycle.measured", {"cycle_id": cycle_id, "tenant_id": tenant_id})
        return measurements

    async def reflect(self, cycle_id: str, tenant_id: str) -> dict[str, Any]:
        cycle = self._get(cycle_id, tenant_id)
        if not cycle:
            return {"error": "cycle not found"}
        predicted_confidence = cycle.reasoning.get("confidence", 0.5)
        actual_success = sum(1 for m in cycle.measurements if isinstance(m, dict) and m.get("status") == "met")
        total_measured = len(cycle.measurements) or 1
        actual_rate = actual_success / total_measured
        gap = abs(predicted_confidence - actual_rate)
        cycle.reflection = {
            "predicted_confidence": predicted_confidence,
            "actual_success_rate": round(actual_rate, 3),
            "gap": round(gap, 3),
            "calibration": "well_calibrated" if gap < 0.2 else "over_confident" if predicted_confidence > actual_rate else "under_confident",
            "measurements_count": len(cycle.measurements),
        }
        cycle.status = "reflected"
        self._publish("ril.cycle.reflected", {"cycle_id": cycle_id, "tenant_id": tenant_id, "gap": gap})
        return cycle.reflection

    async def correct(self, cycle_id: str, tenant_id: str) -> dict[str, Any]:
        cycle = self._get(cycle_id, tenant_id)
        if not cycle:
            return {"error": "cycle not found"}
        calibration = cycle.reflection.get("calibration", "unknown")
        adjustments: list[str] = []
        if calibration == "over_confident":
            adjustments.append("reduce_confidence_threshold")
            adjustments.append("require_more_evidence")
        elif calibration == "under_confident":
            adjustments.append("increase_exploration")
            adjustments.append("lower_evidence_threshold")
        else:
            adjustments.append("maintain_current_strategy")
        cycle.correction = {"calibration": calibration, "adjustments": adjustments, "objective": cycle.objective}
        cycle.status = "corrected"
        self._publish("ril.cycle.corrected", {"cycle_id": cycle_id, "tenant_id": tenant_id})
        return cycle.correction

    async def update(self, cycle_id: str, tenant_id: str) -> dict[str, Any]:
        cycle = self._get(cycle_id, tenant_id)
        if not cycle:
            return {"error": "cycle not found"}
        cycle.resulting_state = {
            "objective": cycle.objective,
            "corrections_applied": cycle.correction.get("adjustments", []),
            "final_calibration": cycle.reflection.get("calibration", "unknown"),
            "observations_count": len(cycle.observations),
            "actions_count": len(cycle.actions),
            "measurements_count": len(cycle.measurements),
        }
        cycle.status = "completed"
        self._publish("ril.cycle.completed", {"cycle_id": cycle_id, "tenant_id": tenant_id})
        return cycle.resulting_state

    async def get_cycle(self, cycle_id: str, tenant_id: str) -> IntelligenceCycle | None:
        return self._get(cycle_id, tenant_id)

    async def list_cycles(self, tenant_id: str) -> list[IntelligenceCycle]:
        return [v for k, v in self._cycles.items() if k.startswith(f"{tenant_id}:")]

    async def replay_cycle(self, cycle_id: str, tenant_id: str) -> dict[str, Any]:
        cycle = self._get(cycle_id, tenant_id)
        if not cycle:
            return {"error": "cycle not found"}
        return {
            "cycle_id": cycle.id,
            "objective": cycle.objective,
            "status": cycle.status,
            "autonomy_level": cycle.autonomy_level,
            "steps": {
                "observations": len(cycle.observations),
                "reasoning": cycle.reasoning,
                "plan": cycle.plan,
                "actions": len(cycle.actions),
                "measurements": len(cycle.measurements),
                "reflection": cycle.reflection,
                "correction": cycle.correction,
                "resulting_state": cycle.resulting_state,
            },
            "context": cycle.context,
        }

    def _get(self, cycle_id: str, tenant_id: str) -> IntelligenceCycle | None:
        return self._cycles.get(self._key(tenant_id, cycle_id))

    def _check_autonomy(self, tenant_id: str, action: str, level: str) -> dict[str, Any]:
        if self._autonomy:
            return self._autonomy.evaluate(tenant_id=tenant_id, action=action, level=level)
        return {"decision": "ALLOW", "reason": "no autonomy engine"}

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


__all__ = ["IntelligenceCycle", "RecursiveIntelligenceEngine"]
