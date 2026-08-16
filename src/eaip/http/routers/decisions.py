"""REST API routes for Decision Intelligence."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from eaip.decisions.engine import DecisionEngine
from eaip.decisions.models import DecisionLog
from eaip.http.dependencies import get_tenant_id

router = APIRouter(prefix="/api/v1/decisions", tags=["decisions"])


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
