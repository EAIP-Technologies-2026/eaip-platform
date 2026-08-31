from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger
from eaip.session.workspace import WorkspaceManager

router = APIRouter(prefix="/workspaces", tags=["workspaces"])
log = get_logger("eaip.http.routers.workspaces")


def _get_manager(request: Request) -> WorkspaceManager:
    mgr = request.app.state.lifecycle.platform.container.try_resolve(WorkspaceManager)
    if mgr is None:
        mgr = WorkspaceManager()
        request.app.state.lifecycle.platform.container.register_instance(WorkspaceManager, mgr)
    return mgr


@router.get("")
async def list_workspaces(
    request: Request,
    _user: dict = Depends(get_current_user),
    owner_id: str | None = None,
):
    mgr = _get_manager(request)
    workspaces = mgr.list_workspaces(owner_id=owner_id)
    return [
        {
            "id": w.workspace_id,
            "name": w.name,
            "ownerId": w.owner_id,
            "status": w.status.value,
            "resourceCount": len(w.resource_ids),
            "sharedWith": list(w.shared_with),
            "createdAt": w.created_at.isoformat(),
            "updatedAt": w.updated_at.isoformat(),
        }
        for w in workspaces
    ]


@router.post("")
async def create_workspace(
    request: Request,
    body: dict[str, Any],
    _user: dict = Depends(get_current_user),
):
    mgr = _get_manager(request)
    workspace_id = body.get("id", f"ws-{uuid.uuid4().hex[:12]}")
    name = body.get("name", "New Workspace")
    owner_id = _user.get("sub", _user.get("id", "unknown"))
    ws = mgr.create_workspace(workspace_id, name, owner_id)
    return {
        "id": ws.workspace_id,
        "name": ws.name,
        "ownerId": ws.owner_id,
        "status": ws.status.value,
        "resourceIds": list(ws.resource_ids),
        "sharedWith": list(ws.shared_with),
        "createdAt": ws.created_at.isoformat(),
        "updatedAt": ws.updated_at.isoformat(),
    }


@router.get("/shared")
async def list_shared_workspaces(
    request: Request,
    _user: dict = Depends(get_current_user),
):
    mgr = _get_manager(request)
    user_id = _user.get("sub", _user.get("id", "unknown"))
    workspaces = mgr.get_shared_workspaces(user_id)
    return [
        {
            "id": w.workspace_id,
            "name": w.name,
            "ownerId": w.owner_id,
            "status": w.status.value,
            "resourceCount": len(w.resource_ids),
            "sharedWith": list(w.shared_with),
            "createdAt": w.created_at.isoformat(),
            "updatedAt": w.updated_at.isoformat(),
        }
        for w in workspaces
    ]


@router.get("/{workspace_id}")
async def get_workspace(
    request: Request,
    workspace_id: str,
    _user: dict = Depends(get_current_user),
):
    mgr = _get_manager(request)
    ws = mgr.get_workspace(workspace_id)
    if ws is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Workspace not found")
    return {
        "id": ws.workspace_id,
        "name": ws.name,
        "ownerId": ws.owner_id,
        "status": ws.status.value,
        "resourceIds": list(ws.resource_ids),
        "sharedWith": list(ws.shared_with),
        "createdAt": ws.created_at.isoformat(),
        "updatedAt": ws.updated_at.isoformat(),
        "metadata": ws.metadata,
    }


@router.put("/{workspace_id}")
async def update_workspace(
    request: Request,
    workspace_id: str,
    body: dict[str, Any],
    _user: dict = Depends(get_current_user),
):
    mgr = _get_manager(request)
    name = body.get("name")
    result = mgr.update_workspace(workspace_id, name=name)
    if not result:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Workspace not found")
    ws = mgr.get_workspace(workspace_id)
    return {
        "id": ws.workspace_id,
        "name": ws.name,
        "status": ws.status.value,
        "updatedAt": ws.updated_at.isoformat(),
    }


@router.post("/{workspace_id}/archive")
async def archive_workspace(
    request: Request,
    workspace_id: str,
    _user: dict = Depends(get_current_user),
):
    mgr = _get_manager(request)
    result = mgr.archive_workspace(workspace_id)
    if not result:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Workspace not found")
    return {"status": "archived", "workspaceId": workspace_id}


@router.post("/{workspace_id}/resources")
async def add_resource(
    request: Request,
    workspace_id: str,
    body: dict[str, Any],
    _user: dict = Depends(get_current_user),
):
    mgr = _get_manager(request)
    resource_id = body.get("resourceId")
    if not resource_id:
        raise HTTPException(status_code=422, detail="resourceId is required")
    result = mgr.add_resource(workspace_id, resource_id)
    if not result:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Workspace not found")
    return {"status": "added", "workspaceId": workspace_id, "resourceId": resource_id}


@router.delete("/{workspace_id}/resources/{resource_id}")
async def remove_resource(
    request: Request,
    workspace_id: str,
    resource_id: str,
    _user: dict = Depends(get_current_user),
):
    mgr = _get_manager(request)
    result = mgr.remove_resource(workspace_id, resource_id)
    if not result:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Workspace or resource not found"
        )
    return {"status": "removed", "workspaceId": workspace_id, "resourceId": resource_id}


@router.post("/{workspace_id}/share")
async def share_workspace(
    request: Request,
    workspace_id: str,
    body: dict[str, Any],
    _user: dict = Depends(get_current_user),
):
    mgr = _get_manager(request)
    user_id = body.get("userId")
    if not user_id:
        raise HTTPException(status_code=422, detail="userId is required")
    result = mgr.share_workspace(workspace_id, user_id)
    if not result:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Workspace not found")
    return {"status": "shared", "workspaceId": workspace_id, "sharedWith": user_id}


@router.post("/{workspace_id}/unshare")
async def unshare_workspace(
    request: Request,
    workspace_id: str,
    body: dict[str, Any],
    _user: dict = Depends(get_current_user),
):
    mgr = _get_manager(request)
    user_id = body.get("userId")
    if not user_id:
        raise HTTPException(status_code=422, detail="userId is required")
    result = mgr.unshare_workspace(workspace_id, user_id)
    if not result:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Workspace or user not found")
    return {"status": "unshared", "workspaceId": workspace_id, "unsharedWith": user_id}
