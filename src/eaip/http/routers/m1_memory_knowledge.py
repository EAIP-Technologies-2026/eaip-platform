from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.memory.organizational import OrganizationalMemoryStore
from eaip.knowledge.temporal import TemporalKnowledgeStore

router = APIRouter(prefix="/m1", tags=["m1"])

def _org_store(req: Request) -> OrganizationalMemoryStore:
    s = req.app.state.lifecycle.platform.container.try_resolve(OrganizationalMemoryStore)
    if s is None:
        s = OrganizationalMemoryStore()
        req.app.state.lifecycle.platform.container.register_instance(OrganizationalMemoryStore, s)
    return s

def _tk_store(req: Request) -> TemporalKnowledgeStore:
    s = req.app.state.lifecycle.platform.container.try_resolve(TemporalKnowledgeStore)
    if s is None:
        s = TemporalKnowledgeStore()
        req.app.state.lifecycle.platform.container.register_instance(TemporalKnowledgeStore, s)
    return s

@router.post("/org-memory", status_code=201)
async def create_org_memory(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    store = _org_store(request)
    rec = store.create(organization_id=tenant_id, content=str(body.get("content", "")), memory_type=str(body.get("memory_type", "enterprise_fact")), subject=str(body.get("subject", "")), source=str(body.get("source", "system")), confidence=float(body.get("confidence", 0.8)), provenance=body.get("provenance"), reference=str(body.get("reference", "")), supersedes=body.get("supersedes"))
    return rec.model_dump(mode="json")

@router.get("/org-memory")
async def list_org_memory(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), memory_type: str = "", subject: str = "") -> list[dict[str, Any]]:
    store = _org_store(request)
    return [r.model_dump(mode="json") for r in store.list_for_tenant(tenant_id, memory_type=memory_type or None, subject=subject or None)]

@router.get("/org-memory/temporal")
async def temporal_org_memory(request: Request, at: str = "", tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    store = _org_store(request)
    try:
        at_dt = datetime.fromisoformat(at) if at else datetime.now(UTC)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid at timestamp")
    return [r.model_dump(mode="json") for r in store.temporal_query(tenant_id, at_dt)]

@router.get("/org-memory/stale")
async def stale_memories(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [r.model_dump(mode="json") for r in _org_store(request).detect_stale(tenant_id)]

@router.get("/org-memory/conflicts")
async def memory_conflicts(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _org_store(request).detect_conflicts(tenant_id)

@router.get("/org-memory/maintenance")
async def maintenance_proposals(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _org_store(request).maintenance_proposals(tenant_id)

@router.post("/temporal-knowledge", status_code=201)
async def create_temporal_knowledge(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    store = _tk_store(request)
    rec = store.create(organization_id=tenant_id, subject=str(body.get("subject", "")), content=str(body.get("content", "")), provenance=body.get("provenance"), supersedes=body.get("supersedes"))
    return rec.model_dump(mode="json")

@router.get("/temporal-knowledge")
async def list_temporal(request: Request, at: str = "", subject: str = "", tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    store = _tk_store(request)
    if at:
        try:
            at_dt = datetime.fromisoformat(at)
        except Exception:
            raise HTTPException(status_code=400, detail="invalid at")
        return [r.model_dump(mode="json") for r in store.temporal_query(tenant_id, at_dt, subject=subject or None)]
    prefix = f"{tenant_id}:"
    all_recs = [v for k, v in store._store.items() if k.startswith(prefix)]
    if subject:
        all_recs = [r for r in all_recs if r.subject == subject]
    return [r.model_dump(mode="json") for r in all_recs]

@router.get("/temporal-knowledge/what-changed")
async def what_changed(request: Request, since: str = "", subject: str = "", tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    try:
        since_dt = datetime.fromisoformat(since) if since else datetime.now(UTC)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid since")
    return [r.model_dump(mode="json") for r in _tk_store(request).what_changed(tenant_id, since_dt, subject=subject or None)]

@router.get("/temporal-knowledge/evolution/{subject}")
async def evolution(request: Request, subject: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [r.model_dump(mode="json") for r in _tk_store(request).evolution(tenant_id, subject)]

@router.post("/kcr/assemble")
async def kcr_assemble(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.knowledge.kcr import KCRService
    svc = KCRService()
    query = str(body.get("query", body.get("q", "")))
    if not query:
        raise HTTPException(status_code=400, detail="query required")
    return await svc.assemble(tenant_id=tenant_id, query=query, max_tokens=int(body.get("max_tokens", 4000)), sources=body.get("sources"))

@router.post("/graph/reasoning/path")
async def graph_path(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.kgraph.temporal_reasoning import TemporalReasoningService
    svc = TemporalReasoningService()
    return await svc.relationship_explanation(str(body.get("source", "")), str(body.get("target", "")))

@router.post("/graph/reasoning/impact/{entity_id}")
async def graph_impact(request: Request, entity_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.kgraph.temporal_reasoning import TemporalReasoningService
    svc = TemporalReasoningService()
    affected = await svc.impact_analysis(entity_id, tenant_id)
    dependencies = await svc.dependency_analysis(entity_id, tenant_id)
    return {"entity_id": entity_id, "tenant_id": tenant_id, "affected": affected, "dependencies": dependencies}

@router.post("/decisions/{decision_id}/evidence")
async def add_evidence(request: Request, decision_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.intelligence.decision_service import DecisionIntelligenceService
    svc = request.app.state.lifecycle.platform.container.try_resolve(DecisionIntelligenceService)
    if not svc:
        raise HTTPException(status_code=503, detail="decision service unavailable")
    rec = svc.add_evidence(decision_id, tenant_id, body.get("evidence") or body)
    if not rec:
        raise HTTPException(status_code=404, detail="decision not found")
    return rec.model_dump(mode="json")

@router.post("/decisions/{decision_id}/assumption")
async def add_assumption(request: Request, decision_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.intelligence.decision_service import DecisionIntelligenceService
    svc = request.app.state.lifecycle.platform.container.try_resolve(DecisionIntelligenceService)
    if not svc:
        raise HTTPException(status_code=503, detail="decision service unavailable")
    rec = svc.add_assumption(decision_id, tenant_id, body.get("assumption") or body)
    if not rec:
        raise HTTPException(status_code=404, detail="decision not found")
    return rec.model_dump(mode="json")

@router.post("/decisions/{decision_id}/reverse")
async def reverse_decision(request: Request, decision_id: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.intelligence.decision_service import DecisionIntelligenceService
    svc = request.app.state.lifecycle.platform.container.try_resolve(DecisionIntelligenceService)
    if not svc:
        raise HTTPException(status_code=503, detail="decision service unavailable")
    rec = svc.reverse(decision_id, tenant_id, str((body or {}).get("reason", "")))
    if not rec:
        raise HTTPException(status_code=404, detail="decision not found")
    return rec.model_dump(mode="json")

@router.post("/decisions/compare")
async def compare_decisions(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.intelligence.decision_service import DecisionIntelligenceService
    svc = request.app.state.lifecycle.platform.container.try_resolve(DecisionIntelligenceService)
    if not svc:
        raise HTTPException(status_code=503, detail="decision service unavailable")
    ids = body.get("decision_ids") or body.get("ids") or []
    if not isinstance(ids, list):
        raise HTTPException(status_code=400, detail="decision_ids required")
    return svc.compare(tenant_id, [str(x) for x in ids])
