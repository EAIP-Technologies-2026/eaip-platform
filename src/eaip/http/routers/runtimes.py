from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/runtimes", tags=["runtimes"])


def _registry(req: Request):
    from eaip.runtime_registry.registry import RuntimeRegistry
    reg = req.app.state.lifecycle.platform.container.try_resolve(RuntimeRegistry)
    if reg is None:
        reg = RuntimeRegistry()
        req.app.state.lifecycle.platform.container.register_instance(RuntimeRegistry, reg)
    return reg


@router.get("")
async def list_runtimes(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    reg = _registry(request)
    return [r.model_dump(mode="json") for r in reg.list_for_tenant(tenant_id)]


@router.post("")
async def register_runtime(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.runtime_registry.models import RuntimeRecord, RuntimeKind
    reg = _registry(request)
    runtime_id = str(body.get("runtime_id") or body.get("runtimeId") or f"rt-{uuid.uuid4().hex[:8]}")
    kind = str(body.get("kind") or "local_runtime")
    try:
        k = RuntimeKind(kind)
    except ValueError:
        k = RuntimeKind.local_runtime
    rec = RuntimeRecord(runtime_id=runtime_id, kind=k, name=str(body.get("name", runtime_id)), capabilities=tuple(body.get("capabilities", [])), tenant_id=tenant_id, metadata=body.get("metadata") or {})
    reg.register(rec)
    return rec.model_dump(mode="json")


@router.get("/{runtime_id}")
async def get_runtime(request: Request, runtime_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _registry(request).get(runtime_id)
    if not rec or (rec.tenant_id != tenant_id and rec.tenant_id != "default"):
        raise HTTPException(status_code=404, detail="runtime not found")
    return rec.model_dump(mode="json")


@router.get("/{runtime_id}/health")
async def runtime_health(request: Request, runtime_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _registry(request).get(runtime_id)
    if not rec:
        raise HTTPException(status_code=404, detail="runtime not found")
    return {"runtime_id": runtime_id, "status": rec.status.value, "kind": rec.kind.value}


@router.post("/schedule")
async def schedule_runtime(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    caps = body.get("capabilities") or body.get("required_capabilities") or []
    caps = [str(c) for c in caps] if isinstance(caps, list) else []
    result = _registry(request).schedule(caps or None, tenant_id=tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="no healthy runtime available")
    return result


@router.post("/{runtime_id}/failover")
async def failover_runtime(request: Request, runtime_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    result = _registry(request).failover(runtime_id, tenant_id=tenant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="failover failed — no compatible runtime")
    return {"failed_runtime": runtime_id, "failover_to": result}


@router.delete("/{runtime_id}")
async def delete_runtime(request: Request, runtime_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    ok = _registry(request).delete(runtime_id)
    if not ok:
        raise HTTPException(status_code=404, detail="runtime not found")
    return {"status": "deleted", "runtime_id": runtime_id}
