from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user

router = APIRouter(prefix="/deployment", tags=["deployment"])


@router.get("/checklist")
async def checklist(request: Request, _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "readiness": {"api": "ready", "db": "check DATABASE_URL", "redis": "check REDIS_URL", "qdrant": "check QDRANT_URL"},
        "liveness": {"api": "/live", "db": "asyncpg pool", "migrations": "alembic current"},
        "backup": {"db": "pg_dump via DATABASE_URL", "qdrant": "snapshot via Qdrant API", "config": "env + secrets vault"},
        "restore": {"db": "psql < dump.sql", "qdrant": "restore snapshot", "audit": "replay audit_chain"},
        "rollback": {"code": "git revert + redeploy", "migrations": "down via m016/m017 if needed"},
        "resource_limits": {"api": "512Mi/500m (request)", "worker": "1Gi/1000m"},
        "classification": {"engineering_ready": True, "deployment_ready": "human_config_required", "human_required": ["prod IdP", "secrets vault", "DNS/TLS", "prod DB/Qdrant", "observability DSN", "connector creds", "legal approval"]},
    }


@router.get("/health-detailed")
async def health_detailed(request: Request, _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.health.reporter import HealthReporter
    reporter = request.app.state.lifecycle.platform.container.try_resolve(HealthReporter)
    if reporter:
        report = await reporter.report()
        return {"status": report.status.value if hasattr(report.status, "value") else str(report.status), "checks": [{"component": c.component, "status": c.status.value if hasattr(c.status, "value") else str(c.status)} for c in (report.children or [])]}
    return {"status": "unknown", "checks": []}
