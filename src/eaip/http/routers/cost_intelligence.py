"""Cost Intelligence API — composes existing AiCostService and AiAnalyticsService."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger

router = APIRouter(
    prefix="/cost", tags=["cost"], dependencies=[Depends(get_current_user)]
)
log = get_logger("eaip.http.routers.cost")


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _get_ai_cost_service(request: Request) -> Any:
    container = request.app.state.lifecycle.platform.container
    return container.try_resolve_by_name("AiCostService")


def _get_ai_analytics_service(request: Request) -> Any:
    container = request.app.state.lifecycle.platform.container
    return container.try_resolve_by_name("AiAnalyticsService")


@router.get("/overview")
async def cost_overview(request: Request):
    """Aggregated cost intelligence overview from existing AI cost and analytics services."""
    cost_svc = _get_ai_cost_service(request)
    analytics_svc = _get_ai_analytics_service(request)

    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    total_requests = 0
    cost_by_model: dict[str, float] = defaultdict(float)
    cost_by_tenant: dict[str, float] = defaultdict(float)
    tokens_by_model: dict[str, int] = defaultdict(int)
    records_count = 0

    if cost_svc:
        records = list(cost_svc._records.values())
        records_count = len(records)
        for r in records:
            total_cost += r.amount
            total_input_tokens += r.input_tokens
            total_output_tokens += r.output_tokens
            cost_by_model[r.model_id] += r.amount
            if r.tenant_id:
                cost_by_tenant[r.tenant_id] += r.amount
            tokens_by_model[r.model_id] += r.input_tokens + r.output_tokens

    model_count = len(cost_by_model)
    total_tokens = total_input_tokens + total_output_tokens
    avg_cost_per_request = _safe_div(total_cost, records_count)

    return {
        "overview": {
            "totalCost": round(total_cost, 4),
            "totalRequests": records_count,
            "totalTokens": total_tokens,
            "inputTokens": total_input_tokens,
            "outputTokens": total_output_tokens,
            "avgCostPerRequest": round(avg_cost_per_request, 6),
            "modelCount": model_count,
            "currency": "USD",
        },
        "byModel": {
            model: {"cost": round(cost, 4), "tokens": tokens_by_model.get(model, 0)}
            for model, cost in sorted(cost_by_model.items(), key=lambda x: x[1], reverse=True)
        },
        "byTenant": {
            tenant: round(cost, 4)
            for tenant, cost in sorted(cost_by_tenant.items(), key=lambda x: x[1], reverse=True)
        },
    }


@router.get("/models")
async def cost_models(request: Request):
    """Per-model cost and usage breakdown."""
    cost_svc = _get_ai_cost_service(request)
    if not cost_svc:
        return {"models": []}

    records = list(cost_svc._records.values())
    model_data: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "totalCost": 0.0,
        "requests": 0,
        "inputTokens": 0,
        "outputTokens": 0,
        "totalTokens": 0,
    })

    for r in records:
        m = model_data[r.model_id]
        m["totalCost"] += r.amount
        m["requests"] += 1
        m["inputTokens"] += r.input_tokens
        m["outputTokens"] += r.output_tokens
        m["totalTokens"] += r.input_tokens + r.output_tokens

    models = []
    for model_id, data in sorted(model_data.items(), key=lambda x: x[1]["totalCost"], reverse=True):
        models.append({
            "modelId": model_id,
            "totalCost": round(data["totalCost"], 4),
            "requests": data["requests"],
            "inputTokens": data["inputTokens"],
            "outputTokens": data["outputTokens"],
            "totalTokens": data["totalTokens"],
            "avgCostPerRequest": round(_safe_div(data["totalCost"], data["requests"]), 6),
            "currency": "USD",
        })

    return {"models": models}


@router.get("/providers")
async def cost_providers(request: Request):
    """Per-provider cost and usage breakdown derived from model cost rates."""
    cost_svc = _get_ai_cost_service(request)
    if not cost_svc:
        return {"providers": []}

    records = list(cost_svc._records.values())
    cost_rates = cost_svc._cost_rates

    provider_data: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "totalCost": 0.0,
        "requests": 0,
        "inputTokens": 0,
        "outputTokens": 0,
        "models": set(),
    })

    for r in records:
        rate = cost_rates.get(r.model_id)
        provider = rate.provider if rate else "unknown"
        p = provider_data[provider]
        p["totalCost"] += r.amount
        p["requests"] += 1
        p["inputTokens"] += r.input_tokens
        p["outputTokens"] += r.output_tokens
        p["models"].add(r.model_id)

    providers = []
    for provider, data in sorted(provider_data.items(), key=lambda x: x[1]["totalCost"], reverse=True):
        providers.append({
            "provider": provider,
            "totalCost": round(data["totalCost"], 4),
            "requests": data["requests"],
            "inputTokens": data["inputTokens"],
            "outputTokens": data["outputTokens"],
            "modelCount": len(data["models"]),
            "currency": "USD",
        })

    return {"providers": providers}


@router.get("/agents")
async def cost_agents(request: Request):
    """Per-agent cost and usage breakdown."""
    cost_svc = _get_ai_cost_service(request)
    if not cost_svc:
        return {"agents": []}

    records = list(cost_svc._records.values())
    agent_data: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "totalCost": 0.0,
        "requests": 0,
        "inputTokens": 0,
        "outputTokens": 0,
    })

    for r in records:
        if r.agent_id:
            a = agent_data[r.agent_id]
            a["totalCost"] += r.amount
            a["requests"] += 1
            a["inputTokens"] += r.input_tokens
            a["outputTokens"] += r.output_tokens

    agents = []
    for agent_id, data in sorted(agent_data.items(), key=lambda x: x[1]["totalCost"], reverse=True):
        agents.append({
            "agentId": agent_id,
            "totalCost": round(data["totalCost"], 4),
            "requests": data["requests"],
            "inputTokens": data["inputTokens"],
            "outputTokens": data["outputTokens"],
            "currency": "USD",
        })

    return {"agents": agents}


@router.get("/workflows")
async def cost_workflows(request: Request):
    """Per-workflow cost and usage breakdown."""
    cost_svc = _get_ai_cost_service(request)
    if not cost_svc:
        return {"workflows": []}

    records = list(cost_svc._records.values())
    wf_data: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "totalCost": 0.0,
        "requests": 0,
        "inputTokens": 0,
        "outputTokens": 0,
    })

    for r in records:
        if r.workflow_id:
            w = wf_data[r.workflow_id]
            w["totalCost"] += r.amount
            w["requests"] += 1
            w["inputTokens"] += r.input_tokens
            w["outputTokens"] += r.output_tokens

    workflows = []
    for wf_id, data in sorted(wf_data.items(), key=lambda x: x[1]["totalCost"], reverse=True):
        workflows.append({
            "workflowId": wf_id,
            "totalCost": round(data["totalCost"], 4),
            "requests": data["requests"],
            "inputTokens": data["inputTokens"],
            "outputTokens": data["outputTokens"],
            "currency": "USD",
        })

    return {"workflows": workflows}


@router.get("/trends")
async def cost_trends(request: Request, days: int = 30):
    """Daily cost and token trends from existing cost records."""
    cost_svc = _get_ai_cost_service(request)
    if not cost_svc:
        return {"trends": []}

    records = list(cost_svc._records.values())
    daily: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "cost": 0.0,
        "requests": 0,
        "inputTokens": 0,
        "outputTokens": 0,
    })

    for r in records:
        day_key = r.timestamp.strftime("%Y-%m-%d")
        d = daily[day_key]
        d["cost"] += r.amount
        d["requests"] += 1
        d["inputTokens"] += r.input_tokens
        d["outputTokens"] += r.output_tokens

    trends = []
    for day, data in sorted(daily.items()):
        trends.append({
            "date": day,
            "cost": round(data["cost"], 4),
            "requests": data["requests"],
            "inputTokens": data["inputTokens"],
            "outputTokens": data["outputTokens"],
            "totalTokens": data["inputTokens"] + data["outputTokens"],
        })

    return {"trends": trends[-days:]}


@router.get("/budgets")
async def cost_budgets(request: Request):
    """Budget status from existing AiCostService budgets."""
    cost_svc = _get_ai_cost_service(request)
    if not cost_svc:
        return {"budgets": []}

    budgets = []
    for budget in cost_svc._budgets.values():
        current_spend = 0.0
        for r in cost_svc._records.values():
            if budget.model_id and r.model_id != budget.model_id:
                continue
            if budget.cost_type and r.cost_type != budget.cost_type:
                continue
            current_spend += r.amount

        pct = _safe_div(current_spend, budget.amount) * 100
        status = "under"
        if pct >= 100:
            status = "exceeded"
        elif pct >= 90:
            status = "critical"
        elif pct >= 80:
            status = "warning"

        budgets.append({
            "id": budget.id,
            "name": budget.name,
            "amount": budget.amount,
            "currentSpend": round(current_spend, 4),
            "percentage": round(pct, 2),
            "status": status,
            "period": budget.period.value,
            "currency": budget.currency,
            "enabled": budget.enabled,
        })

    return {"budgets": budgets}


@router.get("/anomalies")
async def cost_anomalies(request: Request):
    """Cost anomalies derived from existing records by comparing against averages."""
    cost_svc = _get_ai_cost_service(request)
    if not cost_svc:
        return {"anomalies": []}

    records = list(cost_svc._records.values())
    model_costs: dict[str, list[float]] = defaultdict(list)
    for r in records:
        model_costs[r.model_id].append(r.amount)

    anomalies = []
    for model_id, costs in model_costs.items():
        if len(costs) < 2:
            continue
        avg = sum(costs) / len(costs)
        if avg == 0:
            continue
        for cost in costs:
            deviation = cost - avg
            pct = abs(deviation / avg * 100)
            if pct > 50:
                severity = "critical"
            elif pct > 25:
                severity = "high"
            elif pct > 10:
                severity = "medium"
            else:
                continue
            anomalies.append({
                "modelId": model_id,
                "actualCost": round(cost, 4),
                "expectedCost": round(avg, 4),
                "deviation": round(deviation, 4),
                "deviationPercent": round(pct, 2),
                "severity": severity,
            })

    return {"anomalies": anomalies[:20]}


@router.get("/alerts")
async def cost_alerts(request: Request):
    """Budget alerts from existing AiCostService."""
    cost_svc = _get_ai_cost_service(request)
    if not cost_svc:
        return {"alerts": []}

    alerts = []
    for alert in cost_svc._alerts.values():
        alerts.append({
            "id": alert.id,
            "budgetId": alert.budget_id,
            "threshold": alert.threshold,
            "actualSpend": alert.actual_spend,
            "budgetedAmount": alert.budgeted_amount,
            "percentage": alert.percentage,
            "triggeredAt": alert.triggered_at.isoformat(),
            "acknowledged": alert.acknowledged_at is not None,
        })

    return {"alerts": alerts}
