from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user
from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.logging.context import get_logger
from eaip.search.persistence import PostgresSearchRepository

router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(get_current_user)])
log = get_logger("eaip.http.routers.search_persistence")

# Live recent-search buffer shared with search_router suggestions. The durable
# source of truth remains PostgresSearchRepository; this in-memory list only
# mirrors recently saved queries so suggestion endpoints have immediate data.
_recent_searches: list[dict[str, Any]] = []


def _tenant_id(user: dict[str, Any]) -> str:
    return str(
        user.get("tenant_id")
        or user.get("org_id")
        or user.get("organization_id")
        or "default"
    )


def _user_id(user: dict[str, Any]) -> str | None:
    uid = user.get("user_id") or user.get("sub")
    return str(uid) if uid else None


def _get_repo(request: Request) -> PostgresSearchRepository | None:
    try:
        return PostgresSearchRepository(DatabaseConnection)
    except Exception:
        return None


@router.get("/recent")
async def list_recent_searches(
    request: Request, user: dict = Depends(get_current_user), limit: int = 10
):
    repo = _get_repo(request)
    if repo is None:
        return {"searches": [], "total": 0}
    items = await repo.list_recent(_tenant_id(user), _user_id(user), limit)
    return {"searches": items, "total": len(items)}


@router.post("/recent")
async def save_recent_search(
    request: Request, user: dict = Depends(get_current_user), body: dict[str, Any] = None
) -> dict[str, Any]:
    body = body or {}
    repo = _get_repo(request)
    if repo is None:
        return {"status": "error", "detail": "Search persistence not available"}
    search_id = await repo.save_recent(
        tenant_id=_tenant_id(user),
        user_id=_user_id(user),
        query=body.get("query", ""),
        category=body.get("category", ""),
    )
    _recent_searches.append(
        {
            "id": search_id,
            "query": body.get("query", ""),
            "category": body.get("category", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    if len(_recent_searches) > 100:
        _recent_searches.pop(0)
    log.info("search.recent_saved", id=search_id)
    return {"status": "saved", "id": search_id}


@router.get("/saved")
async def list_saved_searches(request: Request, user: dict = Depends(get_current_user)):
    repo = _get_repo(request)
    if repo is None:
        return {"searches": [], "total": 0}
    items = await repo.list_saved(_tenant_id(user), _user_id(user))
    return {"searches": items, "total": len(items)}


@router.post("/saved")
async def save_search(
    request: Request, user: dict = Depends(get_current_user), body: dict[str, Any] = None
) -> dict[str, Any]:
    body = body or {}
    repo = _get_repo(request)
    if repo is None:
        return {"status": "error", "detail": "Search persistence not available"}
    search_id = await repo.save_saved(
        tenant_id=_tenant_id(user),
        user_id=_user_id(user),
        name=body.get("name", ""),
        query=body.get("query", ""),
        category=body.get("category", ""),
        filters=body.get("filters", {}),
    )
    log.info("search.saved_saved", id=search_id)
    return {"status": "saved", "id": search_id}


@router.delete("/saved/{search_id}")
async def delete_saved_search(
    request: Request, search_id: str, user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    repo = _get_repo(request)
    if repo is None:
        return {"status": "error", "detail": "Search persistence not available"}
    deleted = await repo.delete_saved(_tenant_id(user), _user_id(user), search_id)
    return {"status": "deleted" if deleted else "not_found"}
