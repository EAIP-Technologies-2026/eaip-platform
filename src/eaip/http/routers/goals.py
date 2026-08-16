"""REST API routes for Goals."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from eaip.goals.engine import GoalEngine
from eaip.goals.exceptions import GoalNotFoundError, GoalValidationError
from eaip.goals.models import BusinessGoal
from eaip.http.dependencies import get_tenant_id

router = APIRouter(prefix="/api/v1/goals", tags=["goals"])


class CreateGoalRequest(BaseModel):
    goal: BusinessGoal


class UpdateGoalRequest(BaseModel):
    updates: dict[str, Any]


def get_goal_engine(request: Request) -> GoalEngine:
    return request.app.state.lifecycle.platform.container.resolve(GoalEngine)


@router.post("", response_model=BusinessGoal, status_code=status.HTTP_201_CREATED)
async def create_goal(
    req: CreateGoalRequest,
    engine: GoalEngine = Depends(get_goal_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """Create a new business goal."""
    try:
        return await engine.create_goal(req.goal, tenant_id=tenant_id)
    except GoalValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[BusinessGoal])
async def list_goals(
    status: str | None = None,
    owner: str | None = None,
    engine: GoalEngine = Depends(get_goal_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """List goals, optionally filtered by status or owner."""
    return await engine.list_goals(status=status, owner=owner, tenant_id=tenant_id)


@router.get("/{goal_id}", response_model=BusinessGoal)
async def get_goal(
    goal_id: str,
    engine: GoalEngine = Depends(get_goal_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get a specific goal."""
    try:
        return await engine.get_goal(goal_id, tenant_id=tenant_id)
    except GoalNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")


@router.patch("/{goal_id}", response_model=BusinessGoal)
async def update_goal(
    goal_id: str,
    req: UpdateGoalRequest,
    engine: GoalEngine = Depends(get_goal_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """Update a specific goal."""
    try:
        return await engine.update_goal(goal_id, req.updates, tenant_id=tenant_id)
    except GoalNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
