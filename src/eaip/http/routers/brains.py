"""Governed Second Brain lifecycle endpoints."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from eaip.brain.enterprise_brain import EnterpriseBrain
from eaip.brain.persistence import SqlSecondBrainRepository
from eaip.brain.second_brain import SecondBrainService
from eaip.events.store import EventStore
from eaip.http.dependencies import get_current_user
from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.db.migrations import MigrationEngine
from eaip.infrastructure.migrations import load_all_migrations
from eaip.memory.engine import MemoryEngine
from eaip.runtime.mission import MissionRegistry
from eaip.settings.core_settings import PlatformSettings

router = APIRouter(prefix="/brains", tags=["brains"], dependencies=[Depends(get_current_user)])

_MIGRATIONS_READY: bool = False
_MIGRATIONS_LOCK = asyncio.Lock()


async def _ensure_repository() -> SqlSecondBrainRepository | None:
    """Ensure the database pool and migrations are ready, returning a repository.

    Returns ``None`` when no database is available so the service gracefully
    falls back to in-memory state (preserving existing behavior).
    """
    global _MIGRATIONS_READY
    if DatabaseConnection.get_pool() is None:
        try:
            settings = PlatformSettings().db
            await DatabaseConnection.initialize(
                "local",
                dsn=settings.dsn,
                min_size=settings.min_pool_size,
                max_size=settings.max_pool_size,
                statement_cache_size=settings.statement_cache_size,
                max_inactive_connection_lifetime=settings.max_inactive_connection_lifetime,
            )
        except Exception:
            return None

    async with _MIGRATIONS_LOCK:
        if not _MIGRATIONS_READY:
            engine = MigrationEngine(DatabaseConnection, table_name=PlatformSettings().db.migration_table)
            await engine.initialize()
            for migration in load_all_migrations():
                engine.register(migration)
            await engine.run_pending()
            _MIGRATIONS_READY = True
    return SqlSecondBrainRepository()


async def _build_service(request: Request) -> SecondBrainService:
    container = request.app.state.lifecycle.platform.container
    service = container.try_resolve(SecondBrainService)
    if service is not None:
        return service
    repository = await _ensure_repository()
    service = SecondBrainService(
        enterprise_brain=container.try_resolve(EnterpriseBrain),
        mission_registry=container.try_resolve(MissionRegistry),
        memory_engine=container.try_resolve(MemoryEngine),
        event_store=container.try_resolve(EventStore),
        repository=repository,
    )
    container.register_instance(SecondBrainService, service)
    return service


def _owner(user: dict[str, Any]) -> str:
    return str(user.get("sub", user.get("id", "unknown")))


def _organization_id(user: dict[str, Any]) -> str:
    return str(
        user.get("organization_id") or user.get("org_id") or user.get("tenant_id") or ""
    )


async def _brain_or_404(request: Request, brain_id: str, user: dict[str, Any]):
    service = await _build_service(request)
    brain = await service.get(brain_id, _owner(user))
    if brain is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Brain not found")
    return brain


@router.get("/templates")
async def list_brain_templates() -> list[dict[str, Any]]:
    """List editable templates for common business functions."""
    return SecondBrainService().templates_for()


@router.get("")
async def list_brains(
    request: Request, user: dict[str, Any] = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """List brains owned by the authenticated user."""
    return [brain.to_dict() for brain in await (await _build_service(request)).list(_owner(user))]


@router.post("")
async def create_brain(
    request: Request,
    body: dict[str, Any],
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a governed business-function brain from a template or custom config."""
    if not body.get("name") and body.get("template") not in SecondBrainService.templates:
        raise HTTPException(status_code=400, detail="A brain name or valid template is required")
    return (
        await (await _build_service(request)).create(body, _owner(user), _organization_id(user))
    ).to_dict()


@router.get("/{brain_id}")
async def get_brain(
    request: Request,
    brain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Retrieve an inspectable brain command-center snapshot."""
    return (await _brain_or_404(request, brain_id, user)).to_dict()


@router.put("/{brain_id}/config")
async def configure_brain(
    request: Request,
    brain_id: str,
    body: dict[str, Any],
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Update the brain's objectives, rules, sources, tools, and approval policy."""
    brain = await _brain_or_404(request, brain_id, user)
    return (await (await _build_service(request)).configure(brain, body)).to_dict()


@router.delete("/{brain_id}")
async def delete_brain(
    request: Request,
    brain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Delete a brain owned by the authenticated user."""
    removed = await (await _build_service(request)).delete(brain_id, _owner(user))
    if not removed:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Brain not found")
    return {"deleted": True, "id": brain_id}


@router.post("/{brain_id}/query")
async def query_brain(
    request: Request,
    brain_id: str,
    body: dict[str, Any],
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Ask a brain for evidence-backed findings and a governed recommendation."""
    query = str(body.get("query", "")).strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    brain = await _brain_or_404(request, brain_id, user)
    return await (await _build_service(request)).query(brain, query)


@router.post("/{brain_id}/recommendations/{recommendation_id}/approve")
async def approve_recommendation(
    request: Request,
    brain_id: str,
    recommendation_id: str,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Approve a recommendation before mission creation."""
    brain = await _brain_or_404(request, brain_id, user)
    try:
        return await (await _build_service(request)).approve(brain, recommendation_id)
    except PermissionError as exc:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{brain_id}/recommendations/{recommendation_id}/reject")
async def reject_recommendation(
    request: Request,
    brain_id: str,
    recommendation_id: str,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Reject a recommendation, preventing execution."""
    brain = await _brain_or_404(request, brain_id, user)
    try:
        return await (await _build_service(request)).reject_action(brain, recommendation_id)
    except PermissionError as exc:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{brain_id}/recommendations/{recommendation_id}/execute")
async def execute_action(
    request: Request,
    brain_id: str,
    recommendation_id: str,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Execute an approved recommendation — create mission, run, record result."""
    brain = await _brain_or_404(request, brain_id, user)
    try:
        return await (await _build_service(request)).execute_action(brain, recommendation_id)
    except PermissionError as exc:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{brain_id}/recommendations/{recommendation_id}/mission")
async def create_brain_mission(
    request: Request,
    brain_id: str,
    recommendation_id: str,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Create an existing EAIP Mission from an approved recommendation."""
    brain = await _brain_or_404(request, brain_id, user)
    try:
        return await (await _build_service(request)).create_mission(brain, recommendation_id)
    except PermissionError as exc:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{brain_id}/memory")
async def remember_brain_outcome(
    request: Request,
    brain_id: str,
    body: dict[str, Any],
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Record an inspectable Brain memory using the existing MemoryEngine."""
    content = str(body.get("content", "")).strip()
    if not content:
        raise HTTPException(status_code=400, detail="Memory content is required")
    brain = await _brain_or_404(request, brain_id, user)
    return await (await _build_service(request)).remember(brain, content)


@router.get("/{brain_id}/activity")
async def brain_activity(
    request: Request,
    brain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Return the Brain's lifecycle activity."""
    return (await _brain_or_404(request, brain_id, user)).activity


@router.get("/{brain_id}/memory")
async def brain_memory(
    request: Request,
    brain_id: str,
    user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Return memory references recorded by the Brain."""
    brain = await _brain_or_404(request, brain_id, user)
    return [
        {"id": memory_id, "why": "Recorded from a governed Brain outcome."}
        for memory_id in brain.memory_ids
    ]


__all__ = ["router"]
