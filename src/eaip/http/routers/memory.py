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

_DEFAULT_SCOPE = MemoryScope(tenant_id="default")


def _get_engine(request: Request) -> MemoryEngine | None:
    return request.app.state.lifecycle.platform.container.try_resolve(MemoryEngine)


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
async def search_memory(request: Request, q: str = "", prefix: str = ""):
    engine = _get_engine(request)
    if engine is None:
        return []

    query = MemoryQuery(query=q, scopes=(_DEFAULT_SCOPE,), limit=100)
    result = await engine.search_memories(query)
    entries = [_to_entry(r.memory, r.memory.memory_id) for r in result.results]

    if prefix:
        entries = [e for e in entries if e["key"].startswith(prefix)]

    return entries


@router.get("")
async def list_memory(request: Request, prefix: str = ""):
    engine = _get_engine(request)
    if engine is None:
        return []

    items = await engine.store.list_by_scope(_DEFAULT_SCOPE)
    entries = [_to_entry(item, item.memory_id) for item in items]

    if prefix:
        entries = [e for e in entries if e["key"].startswith(prefix)]

    return entries


@router.get("/{memory_id}")
async def get_memory(request: Request, memory_id: str):
    engine = _get_engine(request)
    if engine is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Memory engine not available")

    item = await engine.get_memory(memory_id, _DEFAULT_SCOPE)
    if item is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Memory {memory_id} not found")

    return _to_entry(item, memory_id)


@router.put("/{memory_id}")
async def set_memory(request: Request, memory_id: str, body: dict[str, Any]):
    engine = _get_engine(request)
    if engine is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Memory engine not available")

    value = str(body.get("value", ""))

    existing = await engine.get_memory(memory_id, _DEFAULT_SCOPE)
    if existing is not None:
        item = await engine.update_memory(memory_id, _DEFAULT_SCOPE, content=value)
    else:
        now = utc_now()
        item = MemoryItem(
            memory_id=memory_id,
            memory_type=MemoryType.WORKING,
            scope=_DEFAULT_SCOPE,
            content=value,
            importance=0.5,
            created_at=now,
            updated_at=now,
        )
        try:
            item = await engine.store.create(item)
        except MemoryValidationError:
            item = await engine.update_memory(memory_id, _DEFAULT_SCOPE, content=value)

    return _to_entry(item, memory_id)


@router.delete("/{memory_id}")
async def delete_memory(request: Request, memory_id: str):
    engine = _get_engine(request)
    if engine is None:
        return {"status": "deleted"}

    ok = await engine.delete_memory(memory_id, _DEFAULT_SCOPE)
    return {"status": "deleted" if ok else "not_found"}
