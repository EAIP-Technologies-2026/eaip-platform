"""REST API routes for Intelligence Pulse."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from eaip.http.dependencies import get_tenant_id
from eaip.pulse.engine import PulseEngine
from eaip.pulse.models import PulseMetric

router = APIRouter(prefix="/pulse", tags=["pulse"])


class RecordMetricRequest(BaseModel):
    name: str
    value: float
    dimensions: dict[str, Any] = {}


def get_pulse_engine(request: Request) -> PulseEngine:
    return request.app.state.lifecycle.platform.container.resolve(PulseEngine)


@router.post("/metrics", response_model=PulseMetric, status_code=status.HTTP_201_CREATED)
async def record_metric(
    req: RecordMetricRequest,
    engine: PulseEngine = Depends(get_pulse_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """Record a new pulse metric."""
    return await engine.record_metric(
        name=req.name, value=req.value, dimensions=req.dimensions, tenant_id=tenant_id
    )


@router.get("/metrics/{name}", response_model=list[PulseMetric])
async def list_metrics(
    name: str,
    limit: int = 100,
    engine: PulseEngine = Depends(get_pulse_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """List pulse metrics by name."""
    return await engine.list_metrics(name=name, tenant_id=tenant_id, limit=limit)
