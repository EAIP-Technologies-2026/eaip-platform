"""M9 Executive OS + Departmental Applications."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.executive_os.registry import BriefingService, DepartmentRegistry, KPIRegistry
from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/m9", tags=["m9-executive"])


def _briefing(req: Request) -> BriefingService:
    s = req.app.state.lifecycle.platform.container.try_resolve(BriefingService)
    if s is None:
        s = BriefingService()
        req.app.state.lifecycle.platform.container.register_instance(BriefingService, s)
    return s


def _dept(req: Request) -> DepartmentRegistry:
    r = req.app.state.lifecycle.platform.container.try_resolve(DepartmentRegistry)
    if r is None:
        r = DepartmentRegistry()
        req.app.state.lifecycle.platform.container.register_instance(DepartmentRegistry, r)
    return r


def _kpi(req: Request) -> KPIRegistry:
    r = req.app.state.lifecycle.platform.container.try_resolve(KPIRegistry)
    if r is None:
        r = KPIRegistry()
        req.app.state.lifecycle.platform.container.register_instance(KPIRegistry, r)
    return r


# Executive cockpit — M9-A
@router.get("/executive/cockpit")
async def executive_cockpit(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    briefing = _briefing(request).latest_for_tenant(tenant_id)
    dept = _dept(request)
    kpis = _kpi(request).list_for_tenant(tenant_id)
    return {
        "tenant_id": tenant_id,
        "strategic_health": "healthy",
        "kpi_health": [{"kpi_id": k.kpi_id, "name": k.name, "value": k.value, "target": k.target, "trend": k.trend} for k in kpis[:5]],
        "risk_radar": briefing.risks if briefing else [],
        "opportunity_radar": briefing.opportunities if briefing else [],
        "decision_radar": briefing.decisions if briefing else [],
        "workforce_health": "see /m9/departments/hr",
        "mission_health": "see /api/long-missions",
        "system_health": "see /m8/operations/center",
        "ai_quality": "see /api/evaluation",
        "ai_cost": "see /api/cost_v2",
        "approvals": "see /api/approval_center",
        "recommendations": briefing.recommendations if briefing else [],
        "departments": dept.list_departments(),
    }


# Executive briefing — M9-B
@router.get("/executive/briefing")
async def get_briefing(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    b = _briefing(request).latest_for_tenant(tenant_id)
    if not b:
        b = _briefing(request).generate(tenant_id)
    return b.model_dump(mode="json")


@router.post("/executive/briefing")
async def create_briefing(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    b = _briefing(request).generate(tenant_id, context=body)
    return b.model_dump(mode="json")


# Departments — M9-D through M9-J
@router.get("/departments")
async def list_departments(request: Request, _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _dept(request).list_departments()


@router.get("/departments/{department_id}")
async def get_department(request: Request, department_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), industry: str = "") -> dict[str, Any]:
    try:
        view = _dept(request).get_view(department_id, tenant_id, industry or None)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    data = view.model_dump(mode="json")
    # Enrich with live data from existing engines where available
    kpis = _kpi(request).list_for_tenant(tenant_id, department=department_id)
    data["kpis"] = [k.model_dump(mode="json") for k in kpis]
    # Add synthetic evidence trace
    data["evidence_trace"] = f"tenant={tenant_id} department={department_id} source=memory+knowledge+workforce"
    return data


# KPI — shared across departments
@router.get("/kpi")
async def list_kpi(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), department: str = "") -> list[dict[str, Any]]:
    return [k.model_dump(mode="json") for k in _kpi(request).list_for_tenant(tenant_id, department=department or None)]


@router.post("/kpi")
async def create_kpi(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.executive_os.models import KPIRecord
    kpi = KPIRecord(tenant_id=tenant_id, name=str(body.get("name", "KPI")), value=float(body.get("value", 0)), target=float(body.get("target", 100)), unit=str(body.get("unit", "")), trend=str(body.get("trend", "stable")), department=str(body.get("department", "")))
    _kpi(request).record(kpi)
    return kpi.model_dump(mode="json")


@router.get("/kpi/{kpi_id}")
async def get_kpi(request: Request, kpi_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    k = _kpi(request).get(kpi_id, tenant_id)
    if not k:
        raise HTTPException(status_code=404, detail="kpi not found")
    return k.model_dump(mode="json")


# Synthetic demonstrations — M9-L
@router.get("/departments/synthetic/{enterprise}")
async def synthetic_demo(request: Request, enterprise: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    mapping = {
        "apex": {"enterprise": "Apex Advisory Group", "departments": ["executive", "consultancy"], "industry": "consultancy"},
        "nova": {"enterprise": "Nova Manufacturing Systems", "departments": ["operations", "manufacturing"], "industry": "manufacturing"},
        "meridian": {"enterprise": "Meridian Health Services", "departments": ["healthcare", "compliance"], "industry": "healthcare"},
    }
    info = mapping.get(enterprise.lower(), {"enterprise": enterprise, "departments": ["executive"], "industry": "general"})
    dept = _dept(request)
    views = []
    for d in info["departments"]:
        try:
            v = dept.get_view(d if d in dept.DEPARTMENTS else "executive", tenant_id, info["industry"])
            views.append(v.model_dump(mode="json"))
        except Exception:
            pass
    briefing = _briefing(request).latest_for_tenant(tenant_id)
    if not briefing:
        briefing = _briefing(request).generate(tenant_id, context={"what_changed": [{"item": f"Synthetic demo for {info['enterprise']}", "evidence": "synthetic"}]})
    return {"enterprise": info["enterprise"], "industry": info["industry"], "views": views, "briefing": briefing.model_dump(mode="json"), "synthetic": True}
