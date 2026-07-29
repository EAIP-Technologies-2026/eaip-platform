from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger

router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(get_current_user)])
log = get_logger("eaip.http.routers.search_persistence")

# In-memory stores (replace with PostgresRepository in production)
_recent_searches: list[dict[str, Any]] = []
_saved_searches: list[dict[str, Any]] = []


@router.get("/recent")
async def list_recent_searches(request: Request, limit: int = 10):
    return {"searches": _recent_searches[-limit:]}


@router.post("/recent")
async def save_recent_search(request: Request, body: dict[str, Any]):
    entry = {
        "id": f"srch-{uuid.uuid4().hex[:8]}",
        "query": body.get("query", ""),
        "category": body.get("category", ""),
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }
    _recent_searches.append(entry)
    if len(_recent_searches) > 100:
        _recent_searches.pop(0)
    return {"status": "saved", "id": entry["id"]}


@router.get("/saved")
async def list_saved_searches(request: Request):
    return {"searches": _saved_searches}


@router.post("/saved")
async def save_search(request: Request, body: dict[str, Any]):
    entry = {
        "id": f"saved-{uuid.uuid4().hex[:8]}",
        "query": body.get("query", ""),
        "name": body.get("name", ""),
        "category": body.get("category", ""),
        "filters": body.get("filters", {}),
    }
    _saved_searches.append(entry)
    return {"status": "saved", "id": entry["id"]}


@router.delete("/saved/{search_id}")
async def delete_saved_search(request: Request, search_id: str):
    global _saved_searches
    _saved_searches = [s for s in _saved_searches if s["id"] != search_id]
    return {"status": "deleted"}
