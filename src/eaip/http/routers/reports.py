"""Enterprise Reporting API — composes existing analytics, health, and knowledge
services into standard reports and exports them through the existing ExportEngine
and FormatConverter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from eaip.export.engine import ExportEngine
from eaip.export.exceptions import ExportFailedError, FormatNotSupportedError
from eaip.export.formats import FormatConverter
from eaip.export.models import ReportDefinition
from eaip.http.dependencies import get_current_user
from eaip.http.routers import cost_intelligence, events_router, knowledge, operations_analytics
from eaip.logging.context import get_logger

router = APIRouter(
    prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_user)]
)
log = get_logger("eaip.http.routers.reports")

SUPPORTED_FORMATS: tuple[str, ...] = ("json", "csv", "xlsx", "pdf")

REPORTS: tuple[dict[str, Any], ...] = (
    {
        "id": "operations",
        "name": "Operations Report",
        "description": "Agent, workflow, execution, and event summary rows.",
        "sourceType": "operations",
        "formats": list(SUPPORTED_FORMATS),
    },
    {
        "id": "health",
        "name": "System Health Report",
        "description": "Per-service health status rows.",
        "sourceType": "health",
        "formats": list(SUPPORTED_FORMATS),
    },
    {
        "id": "cost",
        "name": "Cost Intelligence Report",
        "description": "AI cost summary and per-model cost rows.",
        "sourceType": "cost",
        "formats": list(SUPPORTED_FORMATS),
    },
    {
        "id": "knowledge",
        "name": "Knowledge Report",
        "description": "Knowledge collection and document statistics rows.",
        "sourceType": "knowledge",
        "formats": list(SUPPORTED_FORMATS),
    },
    {
        "id": "events",
        "name": "Activity Report",
        "description": "Recent platform activity rows.",
        "sourceType": "events",
        "formats": list(SUPPORTED_FORMATS),
    },
)


def _get_engine(request: Request) -> ExportEngine | None:
    container = request.app.state.lifecycle.platform.container
    return container.try_resolve(ExportEngine)


def _report_name(report_id: str) -> str:
    for r in REPORTS:
        if r["id"] == report_id:
            return str(r["name"])
    return report_id


def _columns_for(rows: list[dict[str, Any]]) -> list[str]:
    columns: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in columns:
                columns.append(key)
    return columns


def _job_to_dict(job: Any) -> dict[str, Any]:
    return {
        "id": job.id,
        "reportId": job.report_id,
        "status": job.status,
        "format": job.format,
        "filters": dict(job.filters),
        "startedAt": job.started_at.isoformat() if job.started_at else None,
        "completedAt": job.completed_at.isoformat() if job.completed_at else None,
        "durationMs": job.duration_ms,
        "fileSizeBytes": job.file_size_bytes,
        "recordCount": job.record_count,
        "error": job.error,
        "outputPath": job.output_path,
    }


def _ensure_reports_registered(engine: ExportEngine | None) -> None:
    if engine is None:
        return
    registered = {r.id for r in engine.list_reports()}
    for r in REPORTS:
        if r["id"] not in registered:
            engine.register_report(
                ReportDefinition(
                    id=r["id"],
                    name=str(r["name"]),
                    description=str(r["description"]),
                    source_type=str(r["sourceType"]),
                    format="json",
                    tags=("enterprise", str(r["sourceType"])),
                )
            )


def _rows_from_operations(data: dict[str, Any]) -> list[dict[str, Any]]:
    overview = data.get("overview", {})
    agents = data.get("agents", {})
    workflows = data.get("workflows", {})
    health = data.get("health", {})
    rows: list[dict[str, Any]] = [
        {
            "resource": "Overview",
            "totalOperations": overview.get("totalOperations", 0),
            "successfulOperations": overview.get("successfulOperations", 0),
            "failedOperations": overview.get("failedOperations", 0),
            "successRate": overview.get("successRate", 0.0),
            "activeOperations": overview.get("activeOperations", 0),
            "uptime": overview.get("uptime", "0s"),
            "status": overview.get("overallStatus", "healthy"),
        },
        {
            "resource": "Agents",
            "total": agents.get("total", 0),
            "running": agents.get("running", 0),
            "idle": agents.get("idle", 0),
            "error": agents.get("error", 0),
            "paused": agents.get("paused", 0),
            "executions": agents.get("totalExecutions", 0),
            "successRate": agents.get("successRate", 0.0),
            "avgLatencyMs": agents.get("avgLatencyMs", 0.0),
        },
        {
            "resource": "Workflows",
            "total": workflows.get("total", 0),
            "active": workflows.get("active", 0),
            "paused": workflows.get("paused", 0),
            "draft": workflows.get("draft", 0),
            "executions": workflows.get("totalExecutions", 0),
            "successRate": workflows.get("successRate", 0.0),
            "avgDurationMs": workflows.get("avgDurationMs", 0.0),
        },
        {
            "resource": "Health",
            "overall": health.get("overall", "healthy"),
            "totalServices": health.get("totalServices", 0),
            "healthy": health.get("healthy", 0),
            "degraded": health.get("degraded", 0),
            "down": health.get("down", 0),
        },
    ]
    for ev in data.get("events", {}).get("recent", [])[:25]:
        rows.append(
            {
                "resource": "Event",
                "eventId": ev.get("id", ""),
                "eventType": ev.get("type", ""),
                "title": ev.get("title", ""),
                "description": ev.get("description", ""),
                "timestamp": ev.get("timestamp", ""),
            }
        )
    return rows


def _rows_from_health(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for svc in data.get("services", []):
        rows.append(
            {
                "service": svc.get("name", ""),
                "status": svc.get("status", ""),
                "message": svc.get("message", ""),
            }
        )
    return rows


def _rows_from_cost(data: dict[str, Any]) -> list[dict[str, Any]]:
    overview = data.get("overview", {})
    rows: list[dict[str, Any]] = [
        {
            "resource": "Overview",
            "totalCost": overview.get("totalCost", 0.0),
            "totalRequests": overview.get("totalRequests", 0),
            "totalTokens": overview.get("totalTokens", 0),
            "inputTokens": overview.get("inputTokens", 0),
            "outputTokens": overview.get("outputTokens", 0),
            "avgCostPerRequest": overview.get("avgCostPerRequest", 0.0),
            "modelCount": overview.get("modelCount", 0),
            "currency": overview.get("currency", "USD"),
        }
    ]
    for model, model_data in data.get("byModel", {}).items():
        rows.append(
            {
                "resource": "Model",
                "model": model,
                "cost": model_data.get("cost", 0.0),
                "tokens": model_data.get("tokens", 0),
            }
        )
    for tenant, cost in data.get("byTenant", {}).items():
        rows.append({"resource": "Tenant", "tenant": tenant, "cost": cost})
    return rows


def _rows_from_knowledge(
    stats: dict[str, Any], collections: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "resource": "Summary",
            "totalDocuments": stats.get("totalDocuments", 0),
            "totalCollections": stats.get("totalCollections", 0),
            "indexedCount": stats.get("indexedCount", 0),
            "pendingCount": stats.get("pendingCount", 0),
            "failedCount": stats.get("failedCount", 0),
        }
    ]
    for c in collections[:50]:
        rows.append(
            {
                "resource": "Collection",
                "name": c.get("name", ""),
                "description": c.get("description", ""),
                "documentCount": c.get("documentCount", 0),
            }
        )
    return rows


def _rows_from_events(activity: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ev in activity[:100]:
        rows.append(
            {
                "id": ev.get("id", ""),
                "type": ev.get("type", ""),
                "action": ev.get("action", ""),
                "message": ev.get("message", ""),
                "timestamp": ev.get("timestamp", ""),
                "status": ev.get("status", ""),
            }
        )
    return rows


async def _get_rows(report_id: str, request: Request) -> list[dict[str, Any]]:
    providers: dict[str, Callable[[Request], Awaitable[list[dict[str, Any]]]]] = {
        "operations": _operations_rows,
        "health": _health_rows,
        "cost": _cost_rows,
        "knowledge": _knowledge_rows,
        "events": _events_rows,
    }
    provider = providers.get(report_id)
    if provider is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Report not found: {report_id}")
    return await provider(request)


async def _operations_rows(request: Request) -> list[dict[str, Any]]:
    data = await operations_analytics.operations_analytics(request)
    return _rows_from_operations(data)


async def _health_rows(request: Request) -> list[dict[str, Any]]:
    data = await operations_analytics.operations_health(request)
    return _rows_from_health(data)


async def _cost_rows(request: Request) -> list[dict[str, Any]]:
    data = await cost_intelligence.cost_overview(request)
    return _rows_from_cost(data)


async def _knowledge_rows(request: Request) -> list[dict[str, Any]]:
    stats = await knowledge.knowledge_stats(request)
    collections = await knowledge.list_collections(request)
    return _rows_from_knowledge(stats, collections)


async def _events_rows(request: Request) -> list[dict[str, Any]]:
    activity = await events_router.list_activity(request, limit=100)
    return _rows_from_events(activity)


@router.get("")
async def list_reports(request: Request):
    """List the standard enterprise report catalog and export capabilities."""
    engine = _get_engine(request)
    _ensure_reports_registered(engine)
    return {
        "reports": list(REPORTS),
        "engineAvailable": engine is not None,
        "formats": list(SUPPORTED_FORMATS),
        "generatedAt": datetime.now(UTC).isoformat(),
    }


@router.get("/jobs")
async def list_export_jobs(request: Request, limit: int = 20):
    """List recent export jobs tracked by the ExportEngine."""
    engine = _get_engine(request)
    if engine is None:
        return {"jobs": [], "total": 0}
    jobs = engine.list_jobs()
    return {"jobs": [_job_to_dict(j) for j in jobs[:limit]], "total": len(jobs)}


@router.get("/jobs/{job_id}")
async def get_export_job(request: Request, job_id: str):
    """Fetch a single export job by id."""
    engine = _get_engine(request)
    if engine is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Export engine unavailable")
    try:
        job = engine.get_job(job_id)
    except Exception as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _job_to_dict(job)


@router.get("/{report_id}/preview")
async def preview_report(request: Request, report_id: str, limit: int = 100):
    """Render report rows from existing platform services."""
    rows = await _get_rows(report_id, request)
    rows = rows[:limit]
    return {
        "reportId": report_id,
        "name": _report_name(report_id),
        "generatedAt": datetime.now(UTC).isoformat(),
        "rowCount": len(rows),
        "columns": _columns_for(rows),
        "rows": rows,
    }


@router.post("/{report_id}/export")
async def export_report(request: Request, report_id: str, body: dict[str, Any] | None = None):
    """Generate report rows and export them through the ExportEngine and FormatConverter."""
    fmt = str((body or {}).get("format", "json")).lower()
    if fmt not in SUPPORTED_FORMATS:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"Unsupported format: {fmt}")

    rows = await _get_rows(report_id, request)
    engine = _get_engine(request)
    job_dict: dict[str, Any] | None = None
    if engine is not None:
        _ensure_reports_registered(engine)
        try:
            job = engine.create_export_job(report_id, format=fmt, filters={"format": fmt})
            job = engine.execute_export(job, data=rows)
            job_dict = _job_to_dict(job)
        except ExportFailedError as exc:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        content = FormatConverter.convert(rows, fmt)
    except FormatNotSupportedError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    content_type = (
        "application/json"
        if fmt == "json"
        else "text/csv"
        if fmt == "csv"
        else "application/octet-stream"
    )
    return {
        "reportId": report_id,
        "name": _report_name(report_id),
        "format": fmt,
        "generatedAt": datetime.now(UTC).isoformat(),
        "rowCount": len(rows),
        "content": content.decode("utf-8") if isinstance(content, bytes) else content,
        "contentType": content_type,
        "job": job_dict,
    }


__all__: list[str] = []
