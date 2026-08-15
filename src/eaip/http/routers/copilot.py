"""HTTP router for EAIP Conductor endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import StreamingResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from eaip.agents.registry import AgentRegistry
from eaip.copilot.anomaly import AnomalyDetector
from eaip.copilot.approvals import ApprovalNotFoundError
from eaip.copilot.marketplace.models import SkillPackageManifest
from eaip.copilot.marketplace.registry import MarketplaceRegistry
from eaip.copilot.memory import GovernedMemoryService, MemoryPolicyError
from eaip.copilot.models import ApprovalRequest, ConductorChatRequest, CopilotTurn
from eaip.copilot.service import ConductorService
from eaip.copilot.skills.engine import SkillExecutionEngine, build_default_skill_registry
from eaip.copilot.skills.models import ConductorSkill, SkillResult
from eaip.copilot.twin import SystemTwinService
from eaip.health.reporter import HealthReporter
from eaip.http.dependencies import get_current_user
from eaip.memory.models import MemoryDomain
from eaip.workflow.registry import WorkflowRegistry

router = APIRouter(prefix="/copilot", tags=["copilot"])

CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]


def _get_service(request: Request) -> ConductorService:
    """Resolve the Conductor service from the platform container."""
    return request.app.state.lifecycle.platform.container.resolve(ConductorService)


@router.post("/chat")
async def copilot_chat(
    request: Request,
    body: ConductorChatRequest,
    user: CurrentUser,
) -> CopilotTurn:
    """Process a single Conductor chat message for the authenticated user."""
    service = _get_service(request)
    return await service.converse(body.message, user)


@router.post("/chat/stream")
async def copilot_chat_stream(
    request: Request,
    body: ConductorChatRequest,
    user: CurrentUser,
) -> StreamingResponse:
    """Stream SSE events for a Conductor chat turn."""
    service = _get_service(request)
    return StreamingResponse(
        service.stream_converse(body.message, user),
        media_type="text/event-stream",
    )


@router.get("/approvals")
async def list_approvals(request: Request, user: CurrentUser) -> list[ApprovalRequest]:
    """List the authenticated user's pending approval requests."""
    service = _get_service(request)
    return await service.list_pending(user)


@router.post("/approvals/{approval_id}/approve")
async def approve_approval(
    request: Request,
    approval_id: str,
    user: CurrentUser,
) -> dict[str, Any]:
    """Approve a pending approval request and execute its tool."""
    service = _get_service(request)
    try:
        approval, result = await service.decide_approval(approval_id, user, approve=True)
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"approval": approval, "result": result}


@router.post("/approvals/{approval_id}/reject")
async def reject_approval(
    request: Request,
    approval_id: str,
    user: CurrentUser,
) -> dict[str, Any]:
    """Reject a pending approval request."""
    service = _get_service(request)
    try:
        approval, result = await service.decide_approval(approval_id, user, approve=False)
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"approval": approval, "result": result}


def _twin_service(request: Request) -> SystemTwinService:
    """Build a System Twin service from the platform container."""
    container = request.app.state.lifecycle.platform.container
    return SystemTwinService(
        health_reporter=container.resolve(HealthReporter),
        agent_registry=container.resolve(AgentRegistry),
        workflow_registry=container.resolve(WorkflowRegistry),
    )


def _memory_service(request: Request) -> GovernedMemoryService:
    """Resolve the single governed memory service from the platform container."""
    service = request.app.state.lifecycle.platform.container.try_resolve(GovernedMemoryService)
    if service is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Memory service unavailable")
    return service


@router.get("/twin")
async def get_system_twin(request: Request, _user: CurrentUser) -> dict[str, Any]:
    """Retrieve normalized System Twin state."""
    state = await _twin_service(request).get_state()
    return state.model_dump()


@router.get("/briefing")
async def get_system_briefing(
    request: Request, _user: CurrentUser
) -> dict[str, Any]:
    """Retrieve executive system briefing summary."""
    briefing = await _twin_service(request).get_briefing()
    return briefing.model_dump()


@router.get("/anomalies")
async def get_anomalies(request: Request, _user: CurrentUser) -> list[dict[str, Any]]:
    """Retrieve active proactive anomaly nudges."""
    state = await _twin_service(request).get_state()
    detector = AnomalyDetector()
    anomalies = detector.analyze(state)
    return [a.model_dump() for a in anomalies]


@router.get("/memory")
async def list_governed_memory(
    request: Request,
    user: CurrentUser,
    q: str = "",
) -> list[dict[str, Any]]:
    """Inspect active memory visible to the authenticated actor."""
    try:
        service = _memory_service(request)
        return [service.serialize(item) for item in await service.list_memories(user, q)]
    except MemoryPolicyError as exc:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/memory/context")
async def get_memory_context(
    request: Request, user: CurrentUser, q: str = "", limit: int = 8
) -> dict[str, Any]:
    """Retrieve bounded historical context, explicitly labelled as memory."""
    try:
        service = _memory_service(request)
        items = await service.retrieve(user, q, limit)
        return {
            "provenance": "MEMORY",
            "current_system_facts_required": True,
            "items": [service.serialize(item) for item in items],
        }
    except MemoryPolicyError as exc:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/memory/{memory_id}")
async def get_governed_memory(
    request: Request,
    memory_id: str,
    user: CurrentUser,
) -> dict[str, Any]:
    """Retrieve one memory only when it is in an authorized derived scope."""
    try:
        service = _memory_service(request)
        item = await service.get(user, memory_id)
    except MemoryPolicyError as exc:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Memory not found")
    return service.serialize(item)


@router.post("/memory")
async def create_governed_memory(
    request: Request, body: dict[str, Any], user: CurrentUser
) -> dict[str, Any]:
    """Create explicit memory with server-derived scope, sensitivity, and retention."""
    try:
        domain = MemoryDomain(str(body.get("domain", MemoryDomain.PERSONAL.value)))
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid memory domain",
        ) from exc
    try:
        service = _memory_service(request)
        item = await service.create(
            user,
            content=str(body.get("content", "")),
            domain=domain,
            importance=float(body.get("importance", 0.6)),
            tags=tuple(str(tag) for tag in body.get("tags", []) if isinstance(tag, str)),
        )
        return service.serialize(item)
    except MemoryPolicyError as exc:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/memory/forget")
async def forget_governed_memory(
    request: Request, body: dict[str, Any], user: CurrentUser
) -> dict[str, Any]:
    """Forget explicitly selected memory; no client scope or policy fields are trusted."""
    try:
        service = _memory_service(request)
        deleted = await service.forget(
            user,
            memory_id=str(body["memory_id"]) if body.get("memory_id") else None,
            query=str(body["query"]) if body.get("query") else None,
        )
        return {"status": "forgotten", "deleted_count": deleted}
    except MemoryPolicyError as exc:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.delete("/memory/{memory_id}")
async def delete_governed_memory(
    request: Request, memory_id: str, user: CurrentUser
) -> dict[str, Any]:
    """Delete one visible memory through the governed deletion policy."""
    try:
        service = _memory_service(request)
        deleted = await service.forget(user, memory_id=memory_id)
    except MemoryPolicyError as exc:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Memory not found")
    return {"status": "forgotten", "id": memory_id}


@router.get("/skills")
async def list_skills(_request: Request, _user: CurrentUser) -> list[ConductorSkill]:
    """List registered Conductor skills."""
    registry = build_default_skill_registry()
    return list(registry.list_skills())


@router.post("/skills/{skill_id}/execute")
async def execute_skill(request: Request, skill_id: str, user: CurrentUser) -> SkillResult:
    """Execute a registered Conductor skill with governance enforcement."""
    container = request.app.state.lifecycle.platform.container
    registry = build_default_skill_registry()
    engine = SkillExecutionEngine(
        registry,
        health_reporter=container.resolve(HealthReporter),
        agent_registry=container.resolve(AgentRegistry),
        workflow_registry=container.resolve(WorkflowRegistry),
    )
    return await engine.execute(skill_id, user)


@router.get("/marketplace/catalog")
async def list_marketplace_catalog(
    _request: Request, _user: CurrentUser
) -> list[SkillPackageManifest]:
    """List available skill packages in the enterprise marketplace catalog."""
    skill_reg = build_default_skill_registry()
    mp_reg = MarketplaceRegistry(skill_reg)
    return list(mp_reg.list_catalog())


@router.get("/marketplace/packages/{package_id}")
async def get_marketplace_package(
    _request: Request, package_id: str, _user: CurrentUser
) -> SkillPackageManifest:
    """Inspect a marketplace skill package."""
    skill_reg = build_default_skill_registry()
    mp_reg = MarketplaceRegistry(skill_reg)
    pkg = mp_reg.get_package(package_id)
    if not pkg:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Package '{package_id}' not found.",
        )
    return pkg


@router.post("/marketplace/packages/{package_id}/install")
async def install_marketplace_package(
    _request: Request, package_id: str, _user: CurrentUser
) -> SkillPackageManifest:
    """Install a marketplace skill package."""
    skill_reg = build_default_skill_registry()
    mp_reg = MarketplaceRegistry(skill_reg)
    return mp_reg.install_package(package_id)


@router.post("/marketplace/packages/{package_id}/enable")
async def enable_marketplace_package(
    _request: Request, package_id: str, _user: CurrentUser
) -> SkillPackageManifest:
    """Enable an installed marketplace skill package."""
    skill_reg = build_default_skill_registry()
    mp_reg = MarketplaceRegistry(skill_reg)
    return mp_reg.enable_package(package_id)


@router.post("/marketplace/packages/{package_id}/disable")
async def disable_marketplace_package(
    _request: Request, package_id: str, _user: CurrentUser
) -> SkillPackageManifest:
    """Disable a marketplace skill package."""
    skill_reg = build_default_skill_registry()
    mp_reg = MarketplaceRegistry(skill_reg)
    return mp_reg.disable_package(package_id)


@router.post("/marketplace/packages/{package_id}/upgrade")
async def upgrade_marketplace_package(
    _request: Request,
    package_id: str,
    new_version: str,
    _user: CurrentUser,
) -> SkillPackageManifest:
    """Upgrade an installed marketplace skill package to a new version."""
    skill_reg = build_default_skill_registry()
    mp_reg = MarketplaceRegistry(skill_reg)
    return mp_reg.upgrade_package(package_id, new_version)



__all__ = ["router"]
