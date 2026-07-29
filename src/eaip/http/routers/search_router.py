from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger

router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(get_current_user)])
log = get_logger("eaip.http.routers.search")


@router.get("")
async def global_search(request: Request, q: str = "", category: str = "", page: int = 1, pageSize: int = 20):
    results = []
    suggestions = []

    if q.strip():
        results = [
            {
                "id": "search-placeholder",
                "title": f"Results for '{q}'",
                "description": "Full search indexing available via EnterpriseSearchEngine",
                "category": category or "general",
                "url": "",
                "score": 1.0,
            }
        ]

    return {
        "results": results,
        "suggestions": suggestions,
        "total": len(results),
        "page": page,
        "pageSize": pageSize,
        "query": q,
    }


@router.get("/suggestions")
async def search_suggestions(request: Request, q: str = ""):
    return {"suggestions": [], "query": q}


@router.get("/recent")
async def recent_searches(request: Request):
    return {"searches": []}


@router.post("/recent")
async def save_recent_search(request: Request, body: dict[str, Any]):
    return {"status": "saved"}


@router.get("/saved")
async def saved_searches(request: Request):
    return {"searches": []}


@router.post("/saved")
async def save_search(request: Request, body: dict[str, Any]):
    return {"status": "saved", "id": "saved-1"}
