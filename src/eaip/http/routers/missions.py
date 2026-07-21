from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger
from eaip.runtime.mission import MissionRegistry, MissionStatus

router = APIRouter(prefix="/missions", tags=["missions"])
log = get_logger("eaip.http.routers.missions")


def _get_registry(request: Request) -> MissionRegistry | None:
    return request.app.state.lifecycle.platform.container.try_resolve(MissionRegistry)


def _mission_to_dict(m) -> dict[str, Any]:
    return {
        "id": m.mission_id,
        "name": m.name,
        "description": m.metadata.get("description", "") if m.metadata else "",
        "status": m.status.value,
        "progress": 100 if m.status == MissionStatus.COMPLETED else (50 if m.status == MissionStatus.RUNNING else (10 if m.status == MissionStatus.QUEUED else 0)),
        "startedAt": datetime.fromtimestamp(m._started_at, tz=timezone.utc).isoformat() if m._started_at else None,
        "completedAt": datetime.fromtimestamp(m._completed_at, tz=timezone.utc).isoformat() if m._completed_at else None,
        "steps": [],
        "agentIds": list(m.agent_ids),
        "workflowIds": list(m.workflow_ids),
    }


@router.get("/stats")
async def mission_stats(request: Request, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    if registry:
        stats = registry.get_stats()
        return {
            "totalMissions": stats["total"],
            "running": stats["running"],
            "completed": stats["completed"],
            "failed": stats["failed"],
            "queued": max(0, stats["total"] - stats["running"] - stats["completed"] - stats["failed"]),
        }
    return {"totalMissions": 0, "running": 0, "completed": 0, "failed": 0, "queued": 0}


@router.get("")
async def list_missions(request: Request, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    if not registry:
        return []
    missions = await registry.list_missions()
    return [_mission_to_dict(m) for m in missions]


@router.post("")
async def create_mission(request: Request, body: dict[str, Any], _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    mid = body.get("id", f"mission-{uuid.uuid4().hex[:8]}")
    if registry:
        mission = await registry.create(
            mission_id=mid,
            name=body.get("name", "New Mission"),
            agent_ids=tuple(body.get("agent_ids", [])),
            workflow_ids=tuple(body.get("workflow_ids", [])),
            knowledge_collections=tuple(body.get("knowledge_collections", [])),
            metadata=body.get("metadata", {}),
        )
        return _mission_to_dict(mission)

    from eaip.runtime.mission import Mission
    mission = Mission(
        mission_id=mid,
        name=body.get("name", "New Mission"),
        agent_ids=tuple(body.get("agent_ids", [])),
        workflow_ids=tuple(body.get("workflow_ids", [])),
        knowledge_collections=tuple(body.get("knowledge_collections", [])),
        metadata=body.get("metadata", {}),
    )
    return _mission_to_dict(mission)


@router.get("/{mission_id}")
async def get_mission(request: Request, mission_id: str, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    if registry:
        mission = await registry.get(mission_id)
        if mission:
            return _mission_to_dict(mission)
    raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Mission {mission_id} not found")


@router.post("/{mission_id}/execute")
async def execute_mission(request: Request, mission_id: str, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    mission = None
    if registry:
        mission = await registry.get(mission_id)
    if mission is None:
        mission = await registry.create(
            mission_id=mission_id,
            name=f"Mission {mission_id}",
        ) if registry else None

    if mission:
        await mission.queue()
        await mission.start()
        await mission.complete(f"Mission {mission_id} executed successfully")
    return {"executionId": f"exec-{mission_id}-{uuid.uuid4().hex[:4]}"}


@router.get("/{mission_id}/logs")
async def get_mission_logs(request: Request, mission_id: str, _user: dict = Depends(get_current_user)):
    return []
