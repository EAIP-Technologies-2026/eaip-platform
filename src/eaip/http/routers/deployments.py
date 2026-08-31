from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger

router = APIRouter(
    prefix="/deployments", tags=["deployments"], dependencies=[Depends(get_current_user)]
)
log = get_logger("eaip.http.routers.deployments")


def _get_manager(request: Request):
    lifecycle = request.app.state.lifecycle
    container = lifecycle.platform.container
    return container.try_resolve("DeploymentManager")


@router.get("")
async def list_deployments(request: Request):
    return []


@router.post("")
async def create_deployment(request: Request, body: dict[str, Any]):
    return {
        "id": f"deploy-{uuid.uuid4().hex[:8]}",
        "status": "deployed",
    }


@router.get("/{deployment_id}")
async def get_deployment(request: Request, deployment_id: str):
    return {
        "id": deployment_id,
        "name": f"Deployment {deployment_id}",
        "status": "active",
        "version": "0.0.2",
        "config": {},
    }


@router.post("/{deployment_id}/rollback")
async def rollback_deployment(request: Request, deployment_id: str):
    return {
        "id": deployment_id,
        "status": "rolled_back",
    }
