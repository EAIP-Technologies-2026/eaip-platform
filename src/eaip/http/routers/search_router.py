"""Search endpoints — global search wired to the existing EnterpriseSearchEngine."""

from __future__ import annotations

import contextlib
from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from eaip.events.store import EventStore
from eaip.http.dependencies import get_current_user
from eaip.http.routers.search_persistence import _recent_searches
from eaip.knowledge.engine import KnowledgeEngine
from eaip.logging.context import get_logger
from eaip.notifications.center import NotificationCenter
from eaip.search.engine import EnterpriseSearchEngine
from eaip.search.models import SearchResultItem, SearchQuery

router = APIRouter(
    prefix="/search", tags=["search"], dependencies=[Depends(get_current_user)]
)
log = get_logger("eaip.http.routers.search")


def _container(request: Request) -> Any:
    """Return the DI container from the request lifecycle."""
    return request.app.state.lifecycle.platform.container


def _get_engine(request: Request) -> EnterpriseSearchEngine | None:
    """Resolve the EnterpriseSearchEngine from the container (if wired)."""
    return _container(request).try_resolve(EnterpriseSearchEngine)


def item_to_dict(item: SearchResultItem, query: str) -> dict[str, Any]:
    """Map a SearchResultItem into the search API contract.

    Adds source, excerpt, timestamp, and score so consumers can render
    result cards without fabricating data.
    """
    meta = dict(item.metadata or {})
    title = item.title or (item.content[:120] if item.content else "Untitled")
    return {
        "id": item.id,
        "title": title,
        "description": item.content[:240],
        "category": item.collection or "knowledge",
        "url": "",
        "score": round(item.score, 4),
        "source": item.source or item.collection or "",
        "excerpt": item.content[:240],
        "timestamp": meta.get("updated_at") or meta.get("created_at") or "",
        "metadata": meta,
        "query": query,
    }


def build_capabilities(
    engine: EnterpriseSearchEngine | None,
    *,
    knowledge_available: bool,
    events_available: bool,
    notifications_available: bool,
) -> dict[str, Any]:
    """Describe which search sources are genuinely available at runtime.

    Prevents the UI from promising universal search when the underlying
    capability is not wired into the running platform.
    """
    providers = list(engine.providers) if engine is not None else []
    return {
        "engineAvailable": engine is not None,
        "sources": [
            {
                "id": "knowledge",
                "available": knowledge_available or "knowledge" in providers,
                "label": "Knowledge",
                "description": "Search indexed knowledge documents",
            },
            {
                "id": "events",
                "available": events_available,
                "label": "Events",
                "description": "Recent platform events and activity",
            },
            {
                "id": "notifications",
                "available": notifications_available,
                "label": "Notifications",
                "description": "Platform notifications",
            },
        ],
    }


def suggestions_from_recent(recent: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Build real query suggestions from recently recorded searches."""
    suggestions: list[dict[str, str]] = []
    seen: set[str] = set()
    for entry in recent:
        text = str(entry.get("query", "")).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        suggestions.append(
            {"text": text, "category": str(entry.get("category", "") or "")}
        )
    return suggestions


@router.get("")
async def global_search(
    request: Request,
    q: str = "",
    category: str = "",
    collection: str = "",
    page: int = 1,
    page_size: int = Query(default=20, alias="pageSize"),
) -> dict[str, Any]:
    """Execute a global search through the wired EnterpriseSearchEngine.

    Only sources registered on the engine are searched. When the engine is
    not available (or the query is empty) an empty result set is returned —
    no placeholder results are fabricated.
    """
    engine = _get_engine(request)
    results: list[dict[str, Any]] = []
    total = 0
    suggestions: list[dict[str, str]] = []

    if engine is not None and q.strip():
        query = SearchQuery(
            query=q.strip(),
            page=max(1, page),
            page_size=max(1, min(page_size, 100)),
        )
        if collection.strip():
            query = query.model_copy(
                update={"collections": (collection.strip(),)}
            )
        with contextlib.suppress(Exception):
            result = await engine.search(query)
            results = [item_to_dict(i, q) for i in result.items]
            total = result.total_count

    if q.strip():
        suggestions = suggestions_from_recent(_recent_searches)

    return {
        "results": results,
        "suggestions": suggestions,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "query": q,
    }


@router.get("/capabilities")
async def search_capabilities(request: Request) -> dict[str, Any]:
    """Report which search sources the running platform can serve."""
    container = _container(request)
    engine = container.try_resolve(EnterpriseSearchEngine)
    return build_capabilities(
        engine,
        knowledge_available=container.try_resolve(KnowledgeEngine) is not None,
        events_available=container.try_resolve(EventStore) is not None,
        notifications_available=container.try_resolve(NotificationCenter)
        is not None,
    )


@router.get("/suggestions")
async def search_suggestions(request: Request, q: str = "") -> dict[str, Any]:
    """Return real query suggestions derived from recent searches."""
    suggestions = suggestions_from_recent(_recent_searches)
    if q.strip():
        needle = q.strip().lower()
        suggestions = [s for s in suggestions if needle in s["text"].lower()]
    return {"suggestions": suggestions[:10], "query": q}


__all__ = ["router"]
