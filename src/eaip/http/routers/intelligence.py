from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.intelligence.cognition import CognitiveEngine
from eaip.intelligence.coordination import CoordinationEngine
from eaip.intelligence.decision_service import DecisionIntelligenceService
from eaip.intelligence.kernel import IntelligenceKernel
from eaip.intelligence.memory_consistency import MemoryConsistencyEngine
from eaip.intelligence.models import CapabilityRecord, IntelligenceContext
from eaip.intelligence.registry import CapabilityRegistry
from eaip.intelligence.supervision import SupervisionEngine

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


def _registry(req: Request) -> CapabilityRegistry:
    reg = req.app.state.lifecycle.platform.container.try_resolve(CapabilityRegistry)
    if reg is None:
        reg = CapabilityRegistry()
        req.app.state.lifecycle.platform.container.register_instance(CapabilityRegistry, reg)
    return reg


def _kernel(req: Request) -> IntelligenceKernel:
    k = req.app.state.lifecycle.platform.container.try_resolve(IntelligenceKernel)
    if k is None:
        k = IntelligenceKernel(registry=_registry(req))
        req.app.state.lifecycle.platform.container.register_instance(IntelligenceKernel, k)
    return k


def _supervision(req: Request) -> SupervisionEngine:
    eng = req.app.state.lifecycle.platform.container.try_resolve(SupervisionEngine)
    if eng is None:
        eng = SupervisionEngine()
        req.app.state.lifecycle.platform.container.register_instance(SupervisionEngine, eng)
    return eng


def _memory(req: Request) -> MemoryConsistencyEngine:
    eng = req.app.state.lifecycle.platform.container.try_resolve(MemoryConsistencyEngine)
    if eng is None:
        eng = MemoryConsistencyEngine()
        req.app.state.lifecycle.platform.container.register_instance(MemoryConsistencyEngine, eng)
    return eng


def _cognition(req: Request) -> CognitiveEngine:
    eng = req.app.state.lifecycle.platform.container.try_resolve(CognitiveEngine)
    if eng is None:
        eng = CognitiveEngine()
        req.app.state.lifecycle.platform.container.register_instance(CognitiveEngine, eng)
    return eng


def _decisions(req: Request) -> DecisionIntelligenceService:
    eng = req.app.state.lifecycle.platform.container.try_resolve(DecisionIntelligenceService)
    if eng is None:
        eng = DecisionIntelligenceService()
        req.app.state.lifecycle.platform.container.register_instance(DecisionIntelligenceService, eng)
    return eng


def _coordination(req: Request) -> CoordinationEngine:
    eng = req.app.state.lifecycle.platform.container.try_resolve(CoordinationEngine)
    if eng is None:
        eng = CoordinationEngine()
        req.app.state.lifecycle.platform.container.register_instance(CoordinationEngine, eng)
    return eng


# Kernel capabilities
@router.get("/kernel/capabilities")
async def list_capabilities(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), q: str = "", category: str = "") -> list[dict[str, Any]]:
    reg = _registry(request)
    if q or category:
        results = reg.search(tenant_id, q, category)
    else:
        results = reg.list_for_tenant(tenant_id)
    return [r.model_dump(mode="json") for r in results]


@router.get("/kernel/capabilities/{capability_id}")
async def get_capability(request: Request, capability_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _registry(request).get(capability_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="capability not found")
    return rec.model_dump(mode="json")


@router.post("/kernel/capabilities")
async def register_capability(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _registry(request)
    cid = str(body.get("capability_id") or body.get("capabilityId") or f"cap-{uuid.uuid4().hex[:8]}")
    rec = CapabilityRecord(capability_id=cid, name=str(body.get("name", cid)), description=str(body.get("description", "")), tenant_id=tenant_id, category=body.get("category", "agent"), metadata=body.get("metadata") or {})
    try:
        rec = CapabilityRecord.model_validate({**body, "capability_id": cid, "tenant_id": tenant_id})
    except Exception:
        pass
    reg.register(rec)
    return rec.model_dump(mode="json")


@router.post("/kernel/executions")
async def kernel_execute(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    capability_id = str(body.get("capability_id") or body.get("capabilityId") or "")
    if not capability_id:
        raise HTTPException(status_code=400, detail="capability_id required")
    ctx = IntelligenceContext(tenant_id=tenant_id, user_id=str(_user.get("sub", "")), goal=str(body.get("goal", "")), task=str(body.get("task", "")), correlation_id=str(body.get("correlation_id") or f"corr-{uuid.uuid4().hex[:8]}"), permissions=tuple(_user.get("roles", [])), budget=body.get("budget") or {})
    kernel = _kernel(request)
    try:
        execution = await kernel.execute(capability_id, ctx, body.get("inputs"))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return execution.model_dump(mode="json")


@router.get("/kernel/executions")
async def list_executions(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    kernel = _kernel(request)
    return [e.model_dump(mode="json") for e in kernel.list_for_tenant(tenant_id)]


@router.get("/kernel/health")
async def kernel_health(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    kernel = _kernel(request)
    return {"tenant_id": tenant_id, **kernel.health()}


# Supervision
@router.post("/supervision")
async def create_supervision(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _supervision(request)
    rec = eng.track(tenant_id=tenant_id, agent_id=str(body.get("agent_id") or body.get("agentId") or ""), goal=str(body.get("goal", "")), mission_id=str(body.get("mission_id") or ""), strategy=str(body.get("strategy", "direct")))
    return rec.model_dump(mode="json")


@router.get("/supervision")
async def list_supervision(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    eng = _supervision(request)
    return [r.model_dump(mode="json") for r in eng.list_for_tenant(tenant_id)]


@router.get("/supervision/{record_id}")
async def get_supervision(request: Request, record_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _supervision(request).get(record_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="supervision record not found")
    return rec.model_dump(mode="json")


@router.post("/supervision/{record_id}/progress")
async def update_progress(request: Request, record_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _supervision(request)
    rec = eng.update_progress(record_id, tenant_id, float(body.get("progress", 0)), float(body.get("confidence", 0)), body.get("warnings"))
    if not rec:
        raise HTTPException(status_code=404, detail="record not found")
    return rec.model_dump(mode="json")


@router.post("/supervision/{record_id}/intervene")
async def intervene(request: Request, record_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    if "admin" not in _user.get("roles", []) and "supervisor" not in _user.get("roles", []):
        pass
    eng = _supervision(request)
    try:
        rec = eng.intervene(record_id, tenant_id, str(body.get("action", "stop")))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not rec:
        raise HTTPException(status_code=404, detail="record not found")
    return rec.model_dump(mode="json")


@router.post("/supervision/{record_id}/predict")
async def predict_failure(request: Request, record_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _supervision(request)
    return eng.predict_failure(record_id, tenant_id)


# Memory consistency
@router.post("/memory/consistency/check")
async def check_consistency(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _memory(request)
    memories = body.get("memories", [])
    knowledge = body.get("knowledge", [])
    report = eng.analyze(tenant_id, memories if isinstance(memories, list) else [], knowledge if isinstance(knowledge, list) else [])
    return report.model_dump(mode="json")


@router.post("/memory/consistency/{report_id}/reconcile")
async def reconcile_report(request: Request, report_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _memory(request)
    try:
        return eng.reconcile(tenant_id, report_id, str(body.get("resolution", "human_review")))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# Cognition
@router.get("/cognition/observe")
async def cognition_observe(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return _cognition(request).observe(tenant_id)


@router.get("/cognition/context")
async def cognition_context(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return _cognition(request).situational_awareness(tenant_id)


@router.post("/cognition/reason")
async def cognition_reason(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _cognition(request)
    hyp = await eng.reason(tenant_id, str(body.get("query", body.get("goal", ""))), str(body.get("strategy", "direct")))
    return hyp.model_dump(mode="json")


@router.post("/cognition/hypotheses")
async def cognition_hypotheses(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    eng = _cognition(request)
    hyps = eng.generate_hypotheses(tenant_id, str(body.get("problem", "")))
    return [h.model_dump(mode="json") for h in hyps]


@router.post("/cognition/evidence/evaluate")
async def cognition_evidence(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    eng = _cognition(request)
    evidence = body.get("evidence", [])
    if not isinstance(evidence, list):
        raise HTTPException(status_code=400, detail="evidence must be a list")
    return eng.evaluate_evidence(evidence)


# Decisions
@router.post("/decisions")
async def create_decision(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _decisions(request)
    rec = eng.create(tenant_id=tenant_id, title=str(body.get("title", "")), objective=str(body.get("objective", "")), context=body.get("context"), criteria=body.get("criteria"))
    return rec.model_dump(mode="json")


@router.get("/decisions")
async def list_decisions(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    eng = _decisions(request)
    return [r.model_dump(mode="json") for r in eng.list_for_tenant(tenant_id)]


@router.get("/decisions/{decision_id}")
async def get_decision(request: Request, decision_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _decisions(request).get(decision_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="decision not found")
    return rec.model_dump(mode="json")


@router.post("/decisions/{decision_id}/alternatives")
async def add_alternatives(request: Request, decision_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _decisions(request)
    alts = body.get("alternatives", body.get("items", []))
    if not isinstance(alts, list):
        raise HTTPException(status_code=400, detail="alternatives must be a list")
    rec = eng.add_alternatives(decision_id, tenant_id, alts)
    if not rec:
        raise HTTPException(status_code=404, detail="decision not found")
    return rec.model_dump(mode="json")


@router.post("/decisions/{decision_id}/evaluate")
async def evaluate_decision(request: Request, decision_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _decisions(request)
    try:
        return eng.evaluate(decision_id, tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/decisions/{decision_id}/simulate")
async def simulate_decision(request: Request, decision_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _decisions(request)
    try:
        return eng.simulate(decision_id, tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/decisions/{decision_id}/approve")
async def approve_decision(request: Request, decision_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _decisions(request)
    rec = eng.approve(decision_id, tenant_id, str(body.get("approver") or _user.get("sub", "unknown")))
    if not rec:
        raise HTTPException(status_code=404, detail="decision not found")
    return rec.model_dump(mode="json")


@router.post("/decisions/{decision_id}/execute")
async def execute_decision(request: Request, decision_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _decisions(request)
    rec = eng.execute(decision_id, tenant_id, str(body.get("execution_id", "")))
    if not rec:
        raise HTTPException(status_code=404, detail="decision not found")
    return rec.model_dump(mode="json")


@router.post("/decisions/{decision_id}/review")
async def review_decision(request: Request, decision_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _decisions(request)
    rec = eng.review(decision_id, tenant_id, str(body.get("actual_outcome", "")), str(body.get("review_status", "reviewed")))
    if not rec:
        raise HTTPException(status_code=404, detail="decision not found")
    return rec.model_dump(mode="json")


# Coordination
@router.post("/coordination/plans")
async def create_plan(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _coordination(request)
    plan = eng.create_plan(tenant_id=tenant_id, objective=str(body.get("objective", "")), priority=str(body.get("priority", "operational")), tasks=body.get("tasks"))
    return plan.model_dump(mode="json")


@router.get("/coordination/plans")
async def list_plans(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    eng = _coordination(request)
    return [p.model_dump(mode="json") for p in eng.list_for_tenant(tenant_id)]


@router.get("/coordination/plans/{plan_id}")
async def get_plan(request: Request, plan_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _coordination(request).get(plan_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="plan not found")
    return rec.model_dump(mode="json")


@router.post("/coordination/plans/{plan_id}/delegate")
async def delegate_plan(request: Request, plan_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _coordination(request)
    rec = eng.delegate(plan_id, tenant_id, body.get("capabilities"))
    if not rec:
        raise HTTPException(status_code=404, detail="plan not found")
    return rec.model_dump(mode="json")


@router.post("/coordination/plans/{plan_id}/resources")
async def allocate_resources(request: Request, plan_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _coordination(request)
    rec = eng.allocate_resources(plan_id, tenant_id, body.get("resources") or body)
    if not rec:
        raise HTTPException(status_code=404, detail="plan not found")
    return rec.model_dump(mode="json")


@router.get("/coordination/plans/{plan_id}/conflicts")
async def get_conflicts(request: Request, plan_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    eng = _coordination(request)
    if not eng.get(plan_id, tenant_id):
        raise HTTPException(status_code=404, detail="plan not found")
    return eng.detect_conflicts(plan_id, tenant_id)


@router.post("/coordination/plans/{plan_id}/verify")
async def verify_outcome(request: Request, plan_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _coordination(request)
    rec = eng.verify_outcome(plan_id, tenant_id, str(body.get("outcome", "")), bool(body.get("success", True)))
    if not rec:
        raise HTTPException(status_code=404, detail="plan not found")
    return rec.model_dump(mode="json")


@router.post("/coordination/plans/{plan_id}/intervene")
async def intervene_plan(request: Request, plan_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _coordination(request)
    rec = eng.intervene(plan_id, tenant_id, str(body.get("action", "pause")))
    if not rec:
        raise HTTPException(status_code=404, detail="plan not found")
    return rec.model_dump(mode="json")
