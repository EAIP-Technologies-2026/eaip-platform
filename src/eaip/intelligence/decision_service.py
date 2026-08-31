from __future__ import annotations

import uuid
from typing import Any

from eaip.intelligence.models import DecisionAlternative, DecisionRecord
from eaip.shared.time import utc_now


class DecisionIntelligenceService:
    def __init__(self, simulation_engine: Any | None = None, event_bus: Any | None = None) -> None:
        self._simulation = simulation_engine
        self._event_bus = event_bus
        self._decisions: dict[str, DecisionRecord] = {}

    def _key(self, tenant_id: str, decision_id: str) -> str:
        return f"{tenant_id}:{decision_id}"

    def create(self, tenant_id: str, title: str, objective: str = "", context: dict[str, Any] | None = None, criteria: dict[str, float] | None = None) -> DecisionRecord:
        decision_id = f"dec-{uuid.uuid4().hex[:8]}"
        rec = DecisionRecord(decision_id=decision_id, tenant_id=tenant_id, title=title, objective=objective, context=context or {}, criteria=criteria or {}, evidence=(), alternatives=(), status="draft")
        self._decisions[self._key(tenant_id, decision_id)] = rec
        self._publish("decision.created", {"decision_id": decision_id, "tenant_id": tenant_id})
        return rec

    def get(self, decision_id: str, tenant_id: str) -> DecisionRecord | None:
        return self._decisions.get(self._key(tenant_id, decision_id))

    def list_for_tenant(self, tenant_id: str) -> list[DecisionRecord]:
        return [v for k, v in self._decisions.items() if k.startswith(f"{tenant_id}:")]

    def add_alternatives(self, decision_id: str, tenant_id: str, alternatives: list[dict[str, Any]]) -> DecisionRecord | None:
        rec = self.get(decision_id, tenant_id)
        if not rec:
            return None
        alts = tuple(DecisionAlternative(name=str(a.get("name", f"alt-{i}")), description=str(a.get("description", "")), expected_outcome=str(a.get("expected_outcome", "")), cost=float(a.get("cost", 0)), risk=float(a.get("risk", 0)), confidence=float(a.get("confidence", 0.5))) for i, a in enumerate(alternatives))
        updated = rec.model_copy(update={"alternatives": alts})
        self._decisions[self._key(tenant_id, decision_id)] = updated
        return updated

    def evaluate(self, decision_id: str, tenant_id: str) -> dict[str, Any]:
        rec = self.get(decision_id, tenant_id)
        if not rec:
            raise ValueError("decision not found")
        if not rec.alternatives:
            return {"decision_id": decision_id, "recommendation": "no alternatives", "scores": {}}
        scores: dict[str, float] = {}
        criteria = rec.criteria or {"cost": 0.3, "risk": 0.3, "confidence": 0.4}
        for alt in rec.alternatives:
            normalized_cost = 1 - min(alt.cost / 100000, 1)
            normalized_risk = 1 - alt.risk
            score = normalized_cost * criteria.get("cost", 0.3) + normalized_risk * criteria.get("risk", 0.3) + alt.confidence * criteria.get("confidence", 0.4)
            scores[alt.name] = round(score, 3)
        best = max(scores, key=lambda k: scores[k]) if scores else ""
        updated = rec.model_copy(update={"recommendation": best, "status": "evaluated"})
        self._decisions[self._key(tenant_id, decision_id)] = updated
        self._publish("decision.recommendation.ready", {"decision_id": decision_id, "tenant_id": tenant_id, "recommendation": best})
        return {"decision_id": decision_id, "scores": scores, "recommendation": best}

    def simulate(self, decision_id: str, tenant_id: str) -> dict[str, Any]:
        rec = self.get(decision_id, tenant_id)
        if not rec:
            raise ValueError("decision not found")
        if not self._simulation:
            return {"decision_id": decision_id, "simulation": "unavailable", "note": "simulation engine not wired"}
        results = []
        has_scenario_engine = hasattr(self._simulation, "run_counterfactual") or hasattr(self._simulation, "create_scenario")
        scenario_engine = None
        if has_scenario_engine:
            scenario_engine = self._simulation
            sim_engine = getattr(scenario_engine, "_simulation", None) or scenario_engine
        else:
            sim_engine = self._simulation
        for alt in rec.alternatives:
            simulated_outcome: dict[str, Any] = {}
            if scenario_engine and hasattr(scenario_engine, "create_scenario"):
                try:
                    baseline = {"decision_id": decision_id, "alternative": alt.name, "cost": alt.cost, "risk": alt.risk, "confidence": alt.confidence}
                    scn_id = scenario_engine.create_scenario(tenant_id, baseline, f"decision-{decision_id}:{alt.name}")
                    cf = scenario_engine.run_counterfactual(scn_id, tenant_id, f"what if we choose {alt.name}? {alt.description}")
                    simulated_outcome = cf.get("simulated_outcome", {})
                    simulated_outcome["_scenario_id"] = scn_id
                    simulated_outcome["_assumption"] = cf.get("assumption", {})
                    simulated_outcome["_confidence"] = cf.get("confidence", 0.5)
                except Exception:
                    tick = sim_engine.tick() if hasattr(sim_engine, "tick") else []
                    simulated_outcome = {"simulated_events": len(tick) if isinstance(tick, list) else 0}
            else:
                tick = sim_engine.tick() if hasattr(sim_engine, "tick") else []
                simulated_outcome = {"simulated_events": len(tick) if isinstance(tick, list) else 0}
            simulated_outcome["alternative"] = alt.name
            simulated_outcome["expected"] = alt.expected_outcome
            simulated_outcome["cost"] = alt.cost
            simulated_outcome["risk"] = alt.risk
            results.append(simulated_outcome)
        predicted = max(results, key=lambda r: r.get("_confidence", r.get("confidence", 0.5)) if isinstance(r.get("_confidence", r.get("confidence", 0)), (int, float)) else 0.5)["alternative"] if results else ""
        if predicted:
            updated = rec.model_copy(update={"evidence": (*rec.evidence, {"type": "simulation", "simulations": results, "predicted": predicted}), "status": "simulated"})
            self._decisions[self._key(tenant_id, decision_id)] = updated
        self._publish("decision.simulation.completed", {"decision_id": decision_id, "tenant_id": tenant_id, "predicted": predicted, "alternatives": len(results)})
        return {"decision_id": decision_id, "simulations": results, "predicted": predicted}

    def approve(self, decision_id: str, tenant_id: str, approver: str) -> DecisionRecord | None:
        rec = self.get(decision_id, tenant_id)
        if not rec:
            return None
        updated = rec.model_copy(update={"approvers": (*rec.approvers, approver), "status": "approved"})
        self._decisions[self._key(tenant_id, decision_id)] = updated
        return updated

    def execute(self, decision_id: str, tenant_id: str, execution_id: str = "") -> DecisionRecord | None:
        rec = self.get(decision_id, tenant_id)
        if not rec:
            return None
        updated = rec.model_copy(update={"execution_id": execution_id or f"exec-{uuid.uuid4().hex[:8]}", "status": "executed"})
        self._decisions[self._key(tenant_id, decision_id)] = updated
        return updated

    def review(self, decision_id: str, tenant_id: str, actual_outcome: str, review_status: str = "reviewed") -> DecisionRecord | None:
        rec = self.get(decision_id, tenant_id)
        if not rec:
            return None
        # predicted vs actual error
        error: float | None = None
        if rec.predicted_outcome and actual_outcome:
            error = 0.0 if rec.predicted_outcome.lower() in actual_outcome.lower() else 1.0
        updated = rec.model_copy(update={"actual_outcome": actual_outcome, "outcome_error": error, "review_status": review_status, "status": "archived"})
        self._decisions[self._key(tenant_id, decision_id)] = updated
        return updated

    def add_evidence(self, decision_id: str, tenant_id: str, evidence: dict[str, Any]) -> DecisionRecord | None:
        rec = self.get(decision_id, tenant_id)
        if not rec:
            return None
        updated = rec.model_copy(update={"evidence": (*rec.evidence, evidence)})
        self._decisions[self._key(tenant_id, decision_id)] = updated
        return updated

    def add_assumption(self, decision_id: str, tenant_id: str, assumption: dict[str, Any]) -> DecisionRecord | None:
        rec = self.get(decision_id, tenant_id)
        if not rec:
            return None
        updated = rec.model_copy(update={"assumptions": (*rec.assumptions, assumption)})
        self._decisions[self._key(tenant_id, decision_id)] = updated
        return updated

    def reverse(self, decision_id: str, tenant_id: str, reason: str = "") -> DecisionRecord | None:
        rec = self.get(decision_id, tenant_id)
        if not rec:
            return None
        updated = rec.model_copy(update={"reversed": True, "status": "reversed", "review_status": f"reversed: {reason}"})
        self._decisions[self._key(tenant_id, decision_id)] = updated
        return updated

    def compare(self, tenant_id: str, decision_ids: list[str]) -> dict[str, Any]:
        recs = [self.get(did, tenant_id) for did in decision_ids]
        recs = [r for r in recs if r]
        return {"tenant_id": tenant_id, "decisions": [r.model_dump(mode="json") for r in recs], "count": len(recs)}

    def quality(self, decision_id: str, tenant_id: str) -> dict[str, Any]:
        rec = self.get(decision_id, tenant_id)
        if not rec:
            raise ValueError("decision not found")
        predicted = rec.recommendation
        sim_predicted = ""
        for ev in rec.evidence:
            if isinstance(ev, dict) and ev.get("type") == "simulation" and ev.get("predicted"):
                sim_predicted = str(ev["predicted"])
                break
        effective_predicted = predicted or sim_predicted
        actual = rec.actual_outcome
        calibration = "unknown" if not actual else ("accurate" if effective_predicted and actual and effective_predicted.lower() in actual.lower() else "inaccurate")
        sim_evidence = next((ev for ev in rec.evidence if isinstance(ev, dict) and ev.get("type") == "simulation"), None)
        predicted_outcome = None
        if sim_evidence:
            sims = sim_evidence.get("simulations", [])
            for s in sims:
                if s.get("alternative") == effective_predicted:
                    predicted_outcome = {k: v for k, v in s.items() if not k.startswith("_")}
                    break
        error: dict[str, Any] = {}
        if predicted_outcome and actual:
            error = {"predicted_alternative": effective_predicted, "actual_outcome": actual, "calibration": calibration}
            if "cost" in predicted_outcome and isinstance(predicted_outcome["cost"], (int, float)):
                error["predicted_cost"] = predicted_outcome["cost"]
        return {"decision_id": decision_id, "predicted": effective_predicted, "sim_predicted": sim_predicted, "actual": actual, "calibration": calibration, "confidence": rec.confidence, "predicted_outcome": predicted_outcome, "error": error, "evidence_count": len(rec.evidence)}

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
