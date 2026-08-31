"""REST API routes for Decision Intelligence."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from eaip.decisions.engine import DecisionEngine
from eaip.decisions.models import DecisionLog
from eaip.http.dependencies import get_tenant_id

router = APIRouter(prefix="/decisions", tags=["decisions"])


class LogDecisionRequest(BaseModel):
    decision_type: str
    context: dict[str, Any] = {}
    outcome: dict[str, Any] = {}


def get_decision_engine(request: Request) -> DecisionEngine:
    return request.app.state.lifecycle.platform.container.resolve(DecisionEngine)


@router.post("/logs", response_model=DecisionLog, status_code=status.HTTP_201_CREATED)
async def log_decision(
    req: LogDecisionRequest,
    engine: DecisionEngine = Depends(get_decision_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """Log a new decision."""
    return await engine.log_decision(
        decision_type=req.decision_type,
        context=req.context,
        outcome=req.outcome,
        tenant_id=tenant_id,
    )


@router.get("/logs/{decision_type}", response_model=list[DecisionLog])
async def list_decisions(
    decision_type: str,
    limit: int = 100,
    engine: DecisionEngine = Depends(get_decision_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """List decision logs by type."""
    return await engine.list_decisions(
        decision_type=decision_type, tenant_id=tenant_id, limit=limit
    )


@router.get("")
async def list_all_decisions(
    limit: int = 50,
    tenant_id: str = Depends(get_tenant_id),
):
    """Recent decision logs for the tenant (authoritative persistence)."""
    from eaip.infrastructure.db.connection import DatabaseConnection

    try:
        rows = await DatabaseConnection.fetch(
            "SELECT id, decision_type, context, outcome, timestamp FROM decision_logs "
            "WHERE tenant_id = $1 ORDER BY timestamp DESC LIMIT $2",
            tenant_id, min(limit, 200),
        )
    except Exception:
        rows = []
    items = []
    for row in rows or []:
        ctx = row["context"] if isinstance(row["context"], dict) else {}
        out = row["outcome"] if isinstance(row["outcome"], dict) else {}
        items.append({
            "id": row["id"],
            "agent": ctx.get("agent", "EAIP"),
            "action": ctx.get("summary", row["decision_type"]),
            "confidence": float(ctx.get("confidence", 0.5)),
            "status": out.get("status", "logged"),
            "riskLevel": ctx.get("risk_level", "low"),
            "timestamp": str(row["timestamp"]),
            "prediction_ref": ctx.get("prediction_ref"),
        })
    return {"tenant_id": tenant_id, "count": len(items), "items": items}
