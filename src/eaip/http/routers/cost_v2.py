from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.cost.tracker import CostTracker
from eaip.cost.models import Category, CostRecord, BudgetPeriod, BudgetScope, CostBudget
from eaip.cost.budgets import BudgetManager
from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/cost-v2", tags=["cost-v2"])


def _tracker(req: Request) -> CostTracker:
    t = req.app.state.lifecycle.platform.container.try_resolve(CostTracker)
    if t is None:
        t = CostTracker()
        req.app.state.lifecycle.platform.container.register_instance(CostTracker, t)
    return t


def _budgets(req: Request) -> BudgetManager:
    bm = req.app.state.lifecycle.platform.container.try_resolve(BudgetManager)
    if bm is None:
        from eaip.cost.alerts import AlertService
        bm = BudgetManager(_tracker(req), AlertService())
        req.app.state.lifecycle.platform.container.register_instance(BudgetManager, bm)
    return bm


@router.post("/record", status_code=201)
async def record_cost(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    tracker = _tracker(request)
    cat = str(body.get("category", "ai"))
    try:
        category = Category(cat)
    except ValueError:
        category = Category.AI
    rec = CostRecord(id=body.get("id") or f"cost-{uuid.uuid4().hex[:6]}", category=category, amount=float(body.get("amount", 0)), currency=str(body.get("currency", "USD")), tenant_id=tenant_id, workflow_id=body.get("workflow_id"), agent_id=body.get("agent_id"), resource_type=body.get("resource_type"), resource_id=body.get("resource_id"), tags=tuple(body.get("tags", [])), metadata={"tenant_id": tenant_id, **(body.get("metadata") or {})})
    await tracker.record_cost(rec)
    return rec.model_dump(mode="json")


@router.get("/summary")
async def cost_summary(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    tracker = _tracker(request)
    by_cat = await tracker.get_cost_by_category(tenant_id=tenant_id)
    total = sum(by_cat.values())
    return {"tenant_id": tenant_id, "total": round(total, 4), "by_category": by_cat, "currency": "USD"}


@router.post("/budgets", status_code=201)
async def create_budget(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    bm = _budgets(request)
    period = str(body.get("period", "monthly"))
    try:
        bp = BudgetPeriod(period)
    except ValueError:
        bp = BudgetPeriod.MONTHLY
    budget = CostBudget(id=body.get("id") or f"bud-{uuid.uuid4().hex[:6]}", name=str(body.get("name", "budget")), amount=float(body.get("amount", 1000)), currency=str(body.get("currency", "USD")), period=bp, scope=BudgetScope.TENANT, scope_id=tenant_id, start_date=datetime.now(UTC), end_date=datetime.now(UTC) + timedelta(days=30))
    created = await bm.create_budget(budget)
    return created.model_dump(mode="json")


@router.post("/check-budget")
async def check_budget(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    bm = _budgets(request)
    estimated = float(body.get("estimated_cost", body.get("amount", 0)))
    budget_id = str(body.get("budget_id", ""))
    if budget_id:
        status = await bm.get_budget_status(budget_id)
        remaining = status["remaining"]
        if estimated > remaining:
            return {"allowed": False, "requires_approval": True, "remaining": remaining, "estimated": estimated}
        return {"allowed": True, "remaining": remaining, "estimated": estimated}
    # tenant total check — warn if near limit
    tracker = _tracker(request)
    total = await tracker.get_total_cost(scope="tenant", scope_id=tenant_id)
    return {"allowed": True, "total_spend": total, "estimated": estimated, "would_be": total + estimated}


@router.get("/forecast")
async def cost_forecast(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), days: int = 30) -> dict[str, Any]:
    tracker = _tracker(request)
    total = await tracker.get_total_cost(scope="tenant", scope_id=tenant_id)
    trend = await tracker.get_cost_trend(scope="tenant", scope_id=tenant_id, interval=timedelta(days=7))
    daily_avg = (total / max(len(trend), 1)) if trend else (total / 30 if total else 0)
    forecast = round(daily_avg * days, 4)
    return {"tenant_id": tenant_id, "actual_total": round(total, 4), "forecast_next_days": days, "estimated_cost": forecast, "note": "forecast distinct from actual — based on historical average"}
