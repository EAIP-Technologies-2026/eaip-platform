from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/swarms", tags=["swarms"])


def _engine(req: Request):
    from eaip.swarm.engine import SwarmEngine
    eng = req.app.state.lifecycle.platform.container.try_resolve(SwarmEngine)
    if eng is None:
        eng = SwarmEngine()
        req.app.state.lifecycle.platform.container.register_instance(SwarmEngine, eng)
    return eng


@router.post("/plan")
async def plan_swarm(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _engine(request)
    goal = str(body.get("goal", ""))
    if not goal:
        raise HTTPException(status_code=400, detail="goal required")
    caps = body.get("capabilities") or body.get("required_capabilities") or []
    caps = [str(c) for c in caps] if isinstance(caps, list) else []
    return eng.plan(goal, caps if caps else None)


@router.post("")
async def create_swarm(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.swarm.models import AutonomyLevel, CollaborationPattern, SwarmDefinition, SwarmTask
    eng = _engine(request)
    swarm_id = str(body.get("swarm_id") or body.get("swarmId") or f"swarm-{uuid.uuid4().hex[:8]}")
    tasks_raw = body.get("tasks", [])
    tasks = tuple(SwarmTask(task_id=str(t.get("task_id") or f"task-{i}"), description=str(t.get("description", "")), assigned_to=str(t.get("assigned_to", "")), fallback_agent=str(t.get("fallback_agent") or t.get("fallbackAgent") or ""), required_capability=str(t.get("required_capability") or t.get("requiredCapability") or ""), risk=str(t.get("risk", "low")), budget=t.get("budget") or {}, dependencies=tuple(t.get("dependencies") or []), expected_output=str(t.get("expected_output") or t.get("expectedOutput") or "")) for i, t in enumerate(tasks_raw))
    pattern = str(body.get("pattern", "parallel"))
    try:
        pat = CollaborationPattern(pattern)
    except ValueError:
        pat = CollaborationPattern.parallel
    autonomy = str(body.get("autonomy_level") or body.get("autonomyLevel") or "SUGGEST")
    try:
        lvl = AutonomyLevel(autonomy)
    except ValueError:
        lvl = AutonomyLevel.suggest
    swarm = SwarmDefinition(swarm_id=swarm_id, tenant_id=tenant_id, name=str(body.get("name", swarm_id)), coordinator=str(body.get("coordinator", "")), specialists=tuple(body.get("specialists", [])), pattern=pat, autonomy_level=lvl, tasks=tasks, consensus_config=body.get("consensus_config") or body.get("consensusConfig") or {}, metadata=body.get("metadata") or {})
    created = eng.create_swarm(swarm)
    return created.model_dump(mode="json")


@router.get("")
async def list_swarms(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    eng = _engine(request)
    return [s.model_dump(mode="json") for s in eng.list_for_tenant(tenant_id)]


@router.get("/{swarm_id}")
async def get_swarm(request: Request, swarm_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _engine(request)
    swarm = eng.get_swarm(swarm_id, tenant_id)
    if not swarm:
        raise HTTPException(status_code=404, detail="swarm not found")
    return swarm.model_dump(mode="json")


@router.post("/{swarm_id}/execute")
async def execute_swarm(request: Request, swarm_id: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _engine(request)
    autonomy = None
    if body and body.get("autonomy_level"):
        from eaip.swarm.models import AutonomyLevel
        try:
            autonomy = AutonomyLevel(str(body["autonomy_level"]))
        except ValueError:
            pass
    try:
        execution = await eng.execute(swarm_id, tenant_id, autonomy_level=autonomy)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return execution.model_dump(mode="json")


@router.get("/executions/list")
async def list_executions(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    eng = _engine(request)
    return [e.model_dump(mode="json") for e in eng.list_executions(tenant_id)]


@router.get("/executions/{execution_id}")
async def get_execution(request: Request, execution_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _engine(request)
    execution = eng.get_execution(execution_id)
    if not execution or execution.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="execution not found")
    return execution.model_dump(mode="json")
