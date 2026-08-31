from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger
from eaip.memory.engine import MemoryEngine
from eaip.memory.exceptions import MemoryValidationError
from eaip.memory.models import MemoryItem, MemoryQuery, MemoryScope, MemoryType
from eaip.shared.time import utc_now

router = APIRouter(prefix="/memory", tags=["memory"], dependencies=[Depends(get_current_user)])
log = get_logger("eaip.http.routers.memory")


def _scope_for_user(user: dict[str, Any]) -> MemoryScope:
    tenant = str(
        user.get("tenant_id")
        or user.get("org_id")
        or user.get("organization_id")
        or user.get("sub")
        or "default"
    )
    uid = user.get("user_id") or user.get("sub")
    return MemoryScope(tenant_id=tenant, user_id=str(uid) if uid else None)


_fallback_engine: MemoryEngine | None = None


def _get_engine(request: Request) -> MemoryEngine | None:
    engine = request.app.state.lifecycle.platform.container.try_resolve(MemoryEngine)
    if engine is not None:
        return engine
    global _fallback_engine
    if _fallback_engine is None:
        from eaip.memory.store import InMemoryStore

        _fallback_engine = MemoryEngine(InMemoryStore())
    return _fallback_engine


def _to_entry(item: MemoryItem, key: str) -> dict[str, Any]:
    return {
        "id": item.memory_id,
        "key": key,
        "value": item.content,
        "timestamp": (item.updated_at or item.created_at).isoformat(),
    }


@router.get("/agents/{agent_id}/graph")
async def memory_graph(agent_id: str):
    return {"nodes": [], "edges": []}


@router.get("/search")
async def search_memory(
    request: Request, user: dict = Depends(get_current_user), q: str = "", prefix: str = ""
):
    engine = _get_engine(request)
    if engine is None:
        return []

    scope = _scope_for_user(user)
    query = MemoryQuery(query=q, scopes=(scope,), limit=100)
    result = await engine.search_memories(query)
    entries = [_to_entry(r.memory, r.memory.memory_id) for r in result.results]

    if prefix:
        entries = [e for e in entries if e["key"].startswith(prefix)]

    return entries


@router.get("")
async def list_memory(request: Request, user: dict = Depends(get_current_user), prefix: str = ""):
    engine = _get_engine(request)
    if engine is None:
        return []

    scope = _scope_for_user(user)
    items = await engine.store.list_by_scope(scope)
    entries = [_to_entry(item, item.memory_id) for item in items]

    if prefix:
        entries = [e for e in entries if e["key"].startswith(prefix)]

    return entries


@router.get("/{memory_id}")
async def get_memory(request: Request, memory_id: str, user: dict = Depends(get_current_user)):
    engine = _get_engine(request)
    if engine is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Memory engine not available")

    scope = _scope_for_user(user)
    item = await engine.get_memory(memory_id, scope)
    if item is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Memory {memory_id} not found")

    return _to_entry(item, memory_id)


@router.put("/{memory_id}")
async def set_memory(
    request: Request,
    memory_id: str,
    user: dict = Depends(get_current_user),
    body: dict[str, Any] = None,
):
    engine = _get_engine(request)
    if engine is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Memory engine not available")

    body = body or {}
    value = str(body.get("value", ""))
    scope = _scope_for_user(user)

    existing = await engine.get_memory(memory_id, scope)
    if existing is not None:
        item = await engine.update_memory(memory_id, scope, content=value)
    else:
        now = utc_now()
        item = MemoryItem(
            memory_id=memory_id,
            memory_type=MemoryType.WORKING,
            scope=scope,
            content=value,
            importance=0.5,
            created_at=now,
            updated_at=now,
        )
        try:
            item = await engine.store.create(item)
        except MemoryValidationError:
            item = await engine.update_memory(memory_id, scope, content=value)

    return _to_entry(item, memory_id)


@router.delete("/{memory_id}")
async def delete_memory(request: Request, memory_id: str, user: dict = Depends(get_current_user)):
    engine = _get_engine(request)
    if engine is None:
        return {"status": "deleted"}

    scope = _scope_for_user(user)
    ok = await engine.delete_memory(memory_id, scope)
    return {"status": "deleted" if ok else "not_found"}
