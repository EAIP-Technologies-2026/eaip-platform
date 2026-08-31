from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.ops_intelligence.service import OpsIntelligenceService
from eaip.logging.context import get_logger

router = APIRouter(prefix="/ops-intelligence", tags=["ops-intelligence"])
log = get_logger("eaip.http.routers.ops_intelligence")


def _service(request: Request) -> OpsIntelligenceService:
    svc = request.app.state.lifecycle.platform.container.try_resolve(OpsIntelligenceService)
    if svc is None:
        svc = OpsIntelligenceService()
        try:
            request.app.state.lifecycle.platform.container.register_instance(OpsIntelligenceService, svc)
        except Exception:
            pass
    return svc


def _insight_to_dict(ins: Any) -> dict[str, Any]:
    return {
        "insight_id": ins.insight_id,
        "insightId": ins.insight_id,
        "tenant_id": ins.tenant_id,
        "tenantId": ins.tenant_id,
        "type": ins.type,
        "severity": ins.severity,
        "evidence": list(ins.evidence),
        "source": ins.source,
        "confidence": ins.confidence,
        "affected_systems": list(ins.affected_systems),
        "affectedSystems": list(ins.affected_systems),
        "recommendation": ins.recommendation,
        "status": ins.status,
        "created_at": ins.created_at.isoformat() if hasattr(ins.created_at, "isoformat") else str(ins.created_at),
        "createdAt": ins.created_at.isoformat() if hasattr(ins.created_at, "isoformat") else str(ins.created_at),
    }


@router.post("/ingest")
async def ingest_events(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _service(request)
    events = body.get("events")
    if events is None:
        if "event" in body:
            events = [body["event"]]
        elif any(k in body for k in ("tenant_id", "tenantId", "type", "event_type", "level", "latency")):
            events = [body]
        else:
            raise HTTPException(status_code=400, detail="events list required")
    if not isinstance(events, list):
        raise HTTPException(status_code=400, detail="events must be a list")
    normalized: list[dict[str, Any]] = []
    for e in events:
        if not isinstance(e, dict):
            raise HTTPException(status_code=400, detail="each event must be an object")
        if "tenant_id" not in e and "tenantId" not in e:
            e = {**e, "tenant_id": tenant_id}
        normalized.append(e)
    insights = svc.ingest_events(normalized)
    tenant_insights = [i for i in insights if i.tenant_id == tenant_id]
    return {"tenant_id": tenant_id, "ingested": len(normalized), "insights": [_insight_to_dict(i) for i in tenant_insights], "count": len(tenant_insights)}


@router.get("/insights")
async def list_insights(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), type: str | None = None, severity: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    svc = _service(request)
    insights = svc.list_for_tenant(tenant_id)
    if type:
        insights = [i for i in insights if i.type == type]
    if severity:
        insights = [i for i in insights if i.severity == severity]
    if status:
        insights = [i for i in insights if i.status == status]
    return [_insight_to_dict(i) for i in insights]


@router.get("/insights/{insight_id}")
async def get_insight(request: Request, insight_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _service(request)
    ins = svc.get(insight_id, tenant_id)
    if not ins:
        raise HTTPException(status_code=404, detail="insight not found")
    return _insight_to_dict(ins)


@router.post("/insights/{insight_id}/escalate")
async def escalate_insight(request: Request, insight_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _service(request)
    ins = svc.escalate(insight_id, tenant_id)
    if not ins:
        raise HTTPException(status_code=404, detail="insight not found")
    return _insight_to_dict(ins)


@router.post("/insights/{insight_id}/acknowledge")
async def acknowledge_insight(request: Request, insight_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _service(request)
    ins = svc.acknowledge(insight_id, tenant_id)
    if not ins:
        raise HTTPException(status_code=404, detail="insight not found")
    return _insight_to_dict(ins)


@router.post("/insights/{insight_id}/close")
async def close_insight(request: Request, insight_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _service(request)
    ins = svc.close(insight_id, tenant_id)
    if not ins:
        raise HTTPException(status_code=404, detail="insight not found")
    return _insight_to_dict(ins)


@router.post("/insights/{insight_id}/decision")
async def insight_to_decision(request: Request, insight_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _service(request)
    ins = svc.get(insight_id, tenant_id)
    if not ins:
        raise HTTPException(status_code=404, detail="insight not found")
    try:
        from eaip.intelligence.decision_service import DecisionIntelligenceService
        dec_svc = request.app.state.lifecycle.platform.container.try_resolve(DecisionIntelligenceService)
        if dec_svc is None:
            dec_svc = DecisionIntelligenceService()
            try:
                request.app.state.lifecycle.platform.container.register_instance(DecisionIntelligenceService, dec_svc)
            except Exception:
                pass
        title = str(body.get("title") or f"Decision for insight {insight_id}")
        objective = str(body.get("objective") or ins.recommendation or f"Address {ins.type} {ins.severity}")
        rec = dec_svc.create(tenant_id=tenant_id, title=title, objective=objective, context={"insight_id": insight_id, "insight_type": ins.type, "severity": ins.severity, "evidence": list(ins.evidence)[:3]})
        return {"insight_id": insight_id, "decision": rec.model_dump(mode="json")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["router"]
