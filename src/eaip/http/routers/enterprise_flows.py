from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.logging.context import get_logger

router = APIRouter(prefix="/enterprise/flows", tags=["enterprise-flows"])
log = get_logger("eaip.http.routers.enterprise_flows")


@router.post("/{enterprise}/trigger")
async def trigger_flow(
    request: Request,
    enterprise: str,
    body: dict[str, Any] | None = None,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    if enterprise not in ("apex", "nova", "meridian"):
        raise HTTPException(status_code=400, detail=f"unknown enterprise {enterprise!r}")
    body = body or {}
    correlation_id = body.get("correlation_id") or str(uuid.uuid4())
    result: dict[str, Any] = {
        "correlation_id": correlation_id,
        "enterprise": enterprise,
        "tenant_id": tenant_id,
        "steps": [],
        "status": "completed",
    }
    try:
        from eaip.knowledge.engine import KnowledgeEngine

        ke = request.app.state.lifecycle.platform.container.try_resolve(KnowledgeEngine)
        if ke is not None:
            try:
                search_result = await ke.search(f"{enterprise} enterprise operations", top_k=3)
                result["steps"].append({"step": "knowledge_search", "status": "completed", "count": len(getattr(search_result, "chunks", []) or [])})
            except Exception as exc:
                result["steps"].append({"step": "knowledge_search", "status": "failed", "error": str(exc)})
        else:
            result["steps"].append({"step": "knowledge_search", "status": "skipped", "reason": "engine not available"})
    except Exception as exc:
        result["steps"].append({"step": "knowledge_search", "status": "failed", "error": str(exc)})

    try:
        from eaip.marketplace.registry import MarketplaceRegistry

        reg = request.app.state.lifecycle.platform.container.try_resolve(MarketplaceRegistry)
        if reg is not None:
            published = reg.all_published()
            relevant = [p for p in published if enterprise.lower() in (p.description or "").lower() or enterprise.lower() in (p.name or "").lower()]
            result["steps"].append({"step": "marketplace_recommend", "status": "completed", "recommendations": len(relevant), "candidates": len(published)})
        else:
            result["steps"].append({"step": "marketplace_recommend", "status": "skipped"})
    except Exception as exc:
        result["steps"].append({"step": "marketplace_recommend", "status": "failed", "error": str(exc)})

    try:
        from eaip.scheduling.service import SchedulingService

        svc = request.app.state.lifecycle.platform.container.try_resolve(SchedulingService)
        if svc is not None:
            from eaip.scheduling.models import ScheduleDefinition, ScheduleKind, ScheduleTargetType, ScheduleTrigger

            schedule = ScheduleDefinition(
                id=f"flow-{enterprise}-{correlation_id[:8]}",
                tenant_id=tenant_id,
                name=f"{enterprise.title()} flow schedule {correlation_id[:8]}",
                target_type=ScheduleTargetType.WORKFLOW,
                target_id=f"workflow-{enterprise}-main",
                trigger=ScheduleTrigger(kind=ScheduleKind.ONE_TIME),
                metadata={"correlation_id": correlation_id, "flow": enterprise},
            )
            try:
                await svc.create_schedule(schedule)
                result["steps"].append({"step": "schedule", "status": "completed", "schedule_id": schedule.id})
            except Exception as exc:
                result["steps"].append({"step": "schedule", "status": "failed", "error": str(exc)})
        else:
            result["steps"].append({"step": "schedule", "status": "skipped"})
    except Exception as exc:
        result["steps"].append({"step": "schedule", "status": "failed", "error": str(exc)})

    try:
        from eaip.workforce.analytics import WorkforceAnalyticsService

        wa = request.app.state.lifecycle.platform.container.try_resolve(WorkforceAnalyticsService)
        if wa is not None:
            overview = wa.get_overview(tenant_id)
            result["steps"].append({"step": "workforce_allocation", "status": "completed", "overview": overview})
        else:
            result["steps"].append({"step": "workforce_allocation", "status": "skipped"})
    except Exception as exc:
        result["steps"].append({"step": "workforce_allocation", "status": "failed", "error": str(exc)})

    try:
        from eaip.kgraph.graph import KnowledgeGraph
        from eaip.kgraph.models import Entity

        kg = request.app.state.lifecycle.platform.container.try_resolve(KnowledgeGraph)
        if kg is not None:
            entity = Entity(
                id=f"flow-{correlation_id[:12]}",
                type=f"flow:{enterprise}",
                name=f"{enterprise.title()} flow {correlation_id[:8]}",
                description=f"Enterprise flow execution for {enterprise}",
                metadata={"tenant_id": tenant_id, "correlation_id": correlation_id},
                tags=(enterprise, "flow"),
            )
            try:
                await kg.add_entity(entity)
                result["steps"].append({"step": "graph_update", "status": "completed", "entity_id": entity.id})
            except Exception as exc:
                if "already exists" in str(exc).lower():
                    result["steps"].append({"step": "graph_update", "status": "completed", "entity_id": entity.id})
                else:
                    result["steps"].append({"step": "graph_update", "status": "failed", "error": str(exc)})
        else:
            result["steps"].append({"step": "graph_update", "status": "skipped"})
    except Exception as exc:
        result["steps"].append({"step": "graph_update", "status": "failed", "error": str(exc)})

    failed = any(s.get("status") == "failed" for s in result["steps"])
    if failed:
        result["status"] = "partial"
    log.info("enterprise.flow.triggered", enterprise=enterprise, tenant_id=tenant_id, correlation_id=correlation_id, status=result["status"])
    return result
