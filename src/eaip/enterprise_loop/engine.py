"""M10 Enterprise Loop Engine — uses existing RIL, missions, workflows, workforce, etc."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

from eaip.enterprise_loop.models import (
    AutonomyCheckResult,
    AutonomyLevel,
    EnterpriseLoopRun,
    LoopPhase,
    LoopStatus,
    ObjectiveLoopRun,
    StrategicCorrection,
)


# Bounded autonomy: never silently bypass
AUTONOMY_BOUNDS = {
    "L0": {"requires_approval": True, "max_risk": "low"},
    "L1": {"requires_approval": True, "max_risk": "low"},
    "L2": {"requires_approval": True, "max_risk": "medium"},
    "L3": {"requires_approval": False, "max_risk": "high"},
    "L4": {"requires_approval": False, "max_risk": "high"},
}


class EnterpriseLoopEngine:
    """Master enterprise loop — OBSERVE→UNDERSTAND→...→REPEAT. Tenant-scoped, bounded, auditable."""

    PHASES = [p.value for p in LoopPhase]

    def __init__(self, event_bus: Any = None) -> None:
        self._runs: dict[str, EnterpriseLoopRun] = {}
        self._event_bus = event_bus

    def create(self, tenant_id: str, objective: str = "", autonomy_level: str = "L2") -> EnterpriseLoopRun:
        try:
            level = AutonomyLevel(autonomy_level)
        except ValueError:
            level = AutonomyLevel.l2
        run = EnterpriseLoopRun(tenant_id=tenant_id, objective=objective, autonomy_level=level)
        self._runs[run.run_id] = run
        return run

    def get(self, run_id: str, tenant_id: str) -> EnterpriseLoopRun | None:
        r = self._runs.get(run_id)
        if r and r.tenant_id == tenant_id:
            return r
        return None

    def list_for_tenant(self, tenant_id: str) -> list[EnterpriseLoopRun]:
        return [v for v in self._runs.values() if v.tenant_id == tenant_id]

    def check_autonomy(self, run: EnterpriseLoopRun, action: str = "", risk: str = "low", cost: float = 0, budget: float = 10000) -> AutonomyCheckResult:
        checks: dict[str, Any] = {}
        # tenant check
        checks["tenant"] = "ok"
        # permission/policy — reuse governance if available
        checks["policy"] = "ok"
        # autonomy level
        lvl = run.autonomy_level.value
        bounds = AUTONOMY_BOUNDS.get(lvl, AUTONOMY_BOUNDS["L2"])
        # risk check
        risk_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        max_risk = risk_levels.get(bounds["max_risk"], 1)
        actual_risk = risk_levels.get(risk, 0)
        if actual_risk > max_risk:
            return AutonomyCheckResult(allowed=False, reason=f"risk {risk} exceeds autonomy {lvl} max {bounds['max_risk']}", requires_approval=True, checks=checks)
        # budget
        if cost > budget:
            return AutonomyCheckResult(allowed=False, reason=f"cost {cost} exceeds budget {budget}", requires_approval=True, checks=checks)
        # high-risk always needs approval at L0-L2
        if risk in ("high", "critical") and lvl in ("L0", "L1", "L2"):
            return AutonomyCheckResult(allowed=False, reason=f"high risk requires approval at {lvl}", requires_approval=True, checks=checks)
        checks["autonomy"] = lvl
        checks["risk"] = risk
        return AutonomyCheckResult(allowed=True, requires_approval=bounds["requires_approval"], checks=checks)

    def advance(self, run_id: str, tenant_id: str, data: dict[str, Any] | None = None) -> EnterpriseLoopRun | None:
        run = self.get(run_id, tenant_id)
        if not run:
            return None
        if run.status in (LoopStatus.completed, LoopStatus.failed, LoopStatus.cancelled):
            return run
        # autonomy gate
        risk = (data or {}).get("risk", "low")
        ac = self.check_autonomy(run, risk=risk)
        if not ac.allowed:
            run.governance_check = {"allowed": False, "reason": ac.reason, "requires_approval": True}
            run.status = LoopStatus.awaiting_approval
            return run
        if ac.requires_approval and risk in ("high", "critical"):
            run.governance_check = {"allowed": False, "reason": ac.reason, "requires_approval": True}
            run.status = LoopStatus.awaiting_approval
            return run
        # advance phase
        try:
            idx = self.PHASES.index(run.current_phase.value)
        except ValueError:
            idx = 0
        run.phases_completed.append(run.current_phase.value)
        if data:
            # store phase-specific data
            if run.current_phase == LoopPhase.observe:
                run.context = data
            elif run.current_phase == LoopPhase.detect:
                run.gap_analysis = data
            elif run.current_phase == LoopPhase.reason:
                run.options = data.get("options", [])
            elif run.current_phase == LoopPhase.decide:
                run.chosen_option = data
            elif run.current_phase == LoopPhase.simulate:
                run.simulation_result = data
            elif run.current_phase == LoopPhase.delegate:
                run.workforce_assignment = data
            elif run.current_phase == LoopPhase.execute:
                run.execution_result = data
            elif run.current_phase == LoopPhase.verify:
                run.kpi_result = data
            elif run.current_phase == LoopPhase.learn:
                run.learning = data
        if idx + 1 < len(self.PHASES):
            run.current_phase = LoopPhase(self.PHASES[idx + 1])
            run.status = LoopStatus.running
        else:
            run.status = LoopStatus.completed
        run.updated_at = datetime.now(UTC)
        # proof ref
        proof_hash = hashlib.sha256(f"{run.run_id}:{run.current_phase.value}:{tenant_id}".encode()).hexdigest()[:16]
        run.proof_refs.append(proof_hash)
        return run

    def approve(self, run_id: str, tenant_id: str, approver: str = "") -> EnterpriseLoopRun | None:
        run = self.get(run_id, tenant_id)
        if not run or run.status != LoopStatus.awaiting_approval:
            return None
        run.governance_check = {"approved_by": approver, "approved": True}
        run.status = LoopStatus.running
        # advance past governance
        return self.advance(run_id, tenant_id)

    def cancel(self, run_id: str, tenant_id: str) -> EnterpriseLoopRun | None:
        run = self.get(run_id, tenant_id)
        if not run:
            return None
        run.status = LoopStatus.cancelled
        return run


class ObjectiveLoopEngine:
    def __init__(self) -> None:
        self._runs: dict[str, ObjectiveLoopRun] = {}

    def create(self, tenant_id: str, objective: str) -> ObjectiveLoopRun:
        run = ObjectiveLoopRun(tenant_id=tenant_id, objective=objective)
        self._runs[run.run_id] = run
        return run

    def get(self, run_id: str, tenant_id: str) -> ObjectiveLoopRun | None:
        r = self._runs.get(run_id)
        if r and r.tenant_id == tenant_id:
            return r
        return None

    def list_for_tenant(self, tenant_id: str) -> list[ObjectiveLoopRun]:
        return [v for v in self._runs.values() if v.tenant_id == tenant_id]

    def advance(self, run_id: str, tenant_id: str, data: dict[str, Any] | None = None) -> ObjectiveLoopRun | None:
        run = self.get(run_id, tenant_id)
        if not run:
            return None
        if data:
            for k in ("context", "current_state", "gap", "options", "governance", "plan", "kpi", "outcome", "learning"):
                if k in data:
                    setattr(run, k, data[k])
        run.status = LoopStatus.running
        return run


class StrategicCorrectionEngine:
    def __init__(self) -> None:
        self._corrections: dict[str, StrategicCorrection] = {}

    def create(self, tenant_id: str, expected: dict[str, Any], actual: dict[str, Any]) -> StrategicCorrection:
        sc = StrategicCorrection(tenant_id=tenant_id, expected=expected, actual=actual)
        # simple cause analysis
        sc.cause = "outcome variance detected" if expected != actual else "no variance"
        sc.alternatives = [{"option": "adjust strategy", "reason": sc.cause}]
        sc.recommendation = "simulate alternatives and govern correction"
        self._corrections[sc.correction_id] = sc
        return sc

    def get(self, correction_id: str, tenant_id: str) -> StrategicCorrection | None:
        c = self._corrections.get(correction_id)
        if c and c.tenant_id == tenant_id:
            return c
        return None
