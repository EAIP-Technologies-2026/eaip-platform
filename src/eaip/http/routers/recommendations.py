"""REST API routes for Recommendations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from eaip.http.dependencies import get_tenant_id
from eaip.recommendations.engine import RecommendationEngine
from eaip.recommendations.models import Recommendation, RecommendationStatus

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


class CreateRecommendationRequest(BaseModel):
    title: str
    description: str
    score: float
    metadata: dict[str, Any] = {}


class UpdateRecommendationStatusRequest(BaseModel):
    status: RecommendationStatus


def get_recommendation_engine(request: Request) -> RecommendationEngine:
    return request.app.state.lifecycle.platform.container.resolve(RecommendationEngine)


@router.post("", response_model=Recommendation, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    req: CreateRecommendationRequest,
    engine: RecommendationEngine = Depends(get_recommendation_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """Create a new recommendation."""
    return await engine.create_recommendation(
        title=req.title,
        description=req.description,
        score=req.score,
        metadata=req.metadata,
        tenant_id=tenant_id,
    )


@router.get("/pending", response_model=list[Recommendation])
async def list_pending_recommendations(
    limit: int = 100,
    engine: RecommendationEngine = Depends(get_recommendation_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """List pending recommendations."""
    return await engine.list_pending(tenant_id=tenant_id, limit=limit)


@router.patch("/{rec_id}/status", response_model=Recommendation)
async def update_recommendation_status(
    rec_id: str,
    req: UpdateRecommendationStatusRequest,
    engine: RecommendationEngine = Depends(get_recommendation_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """Update recommendation status."""
    try:
        return await engine.update_status(rec_id=rec_id, status=req.status, tenant_id=tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
