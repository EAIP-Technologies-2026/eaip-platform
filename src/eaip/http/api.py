from __future__ import annotations

import os
import time

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from eaip._version import __version__
from eaip.app.lifecycle import ApplicationLifecycle
from eaip.health.checks import HealthStatus
from eaip.health.reporter import HealthReporter
from eaip.http.schemas import (
    API_CONTACT,
    API_DESCRIPTION,
    API_LICENSE,
    API_TITLE,
)
from eaip.http.routers import (
    admin,
    administration_center,
    agents,
    auth,
    automation,
    brains,
    copilot,
    cost_intelligence,
    deployments,
    events_router,
    goals,
    governance,
    investigations,
    kgraph,
    knowledge,
    marketplace_routes,
    memory,
    mission_analytics,
    missions,
    monitoring_routes,
    notifications_router,
    operations_analytics,
    orchestrations,
    organizations,
    reports,
    runtime,
    search_persistence,
    search_router,
    system_routes,
    tour,
    websocket,
    workflow_designer,
    workflow_export,
    workflow_versions,
    workflows,
    workforce,
    workspaces,
    pulse,
    decisions,
    recommendations,
)
from eaip.integrations.sentry import add_sentry_middleware, init_sentry
from eaip.logging.context import get_logger

log = get_logger("eaip.http.api")


def _status_text(status: HealthStatus) -> str:
    return status.value if hasattr(status, "value") else str(status)


def create_app(lifecycle: ApplicationLifecycle) -> FastAPI:
    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=__version__,
        contact=API_CONTACT,
        license_info=API_LICENSE,
        lifespan=None,
    )

    # Initialise Sentry error tracking if configured.
    init_sentry(lifecycle.platform.settings)

    # Add Sentry middleware for error capture.
    add_sentry_middleware(app)

    # CORS: restrict to configured origins; development defaults to localhost
    cors_origins = os.environ.get(
        "EAIP_CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,http://localhost:3004",
    ).split(",")
    cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )

    # Security headers middleware
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = (
                "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
            )
            if os.environ.get("EAIP_ENVIRONMENT") == "production":
                response.headers["Strict-Transport-Security"] = (
                    "max-age=63072000; includeSubDomains; preload"
                )
            return response

    app.add_middleware(SecurityHeadersMiddleware)

    app.state.lifecycle = lifecycle
    app.state._start_time = time.time()

    @app.get("/health")
    async def health():
        reporter: HealthReporter = lifecycle.platform.health
        report = await reporter.report()

        infra_checks = []
        if lifecycle._infrastructure and lifecycle._infrastructure._infra_health:
            try:
                infra_report = await lifecycle._infrastructure._infra_health.check()
                infra_checks = [
                    {
                        "component": "infrastructure",
                        "status": infra_report.status.value,
                        "message": infra_report.message,
                        "details": infra_report.details,
                    }
                ]
            except Exception:
                pass

        bg_tasks = []
        if lifecycle._infrastructure:
            bg_tasks = lifecycle._infrastructure.background_tasks.status()

        healthy = report.status in (
            HealthStatus.HEALTHY,
            HealthStatus.SKIPPED,
            HealthStatus.DEGRADED,
        )
        body = {
            "status": _status_text(report.status),
            "message": report.message,
            "checks": [
                {
                    "component": c.component,
                    "status": _status_text(c.status),
                    "message": c.message,
                    "criticality": c.criticality.value if c.criticality else None,
                    "configured": c.configured,
                }
                for c in report.children
            ]
            + infra_checks,
            "background_tasks": bg_tasks,
        }
        status_code = 200 if healthy else 503
        return JSONResponse(content=body, status_code=status_code)

    @app.get("/metrics")
    async def metrics():
        from fastapi.responses import PlainTextResponse
        if hasattr(lifecycle.platform.metrics, "export"):
            return PlainTextResponse(lifecycle.platform.metrics.export())
        else:
            from eaip.metrics.export import prometheus_text
            return PlainTextResponse(prometheus_text([]))

    @app.get("/ready")
    async def ready():
        reporter: HealthReporter = lifecycle.platform.health
        report = await reporter.readiness()
        ready = report.status is HealthStatus.HEALTHY
        body = {
            "status": _status_text(report.status),
            "message": report.message,
            "checks": [
                {
                    "component": c.component,
                    "status": _status_text(c.status),
                    "message": c.message,
                    "criticality": c.criticality.value if c.criticality else None,
                    "configured": c.configured,
                }
                for c in report.children
            ],
        }
        status_code = 200 if ready else 503
        return JSONResponse(content=body, status_code=status_code)

    @app.get("/live")
    async def live():
        reporter: HealthReporter = lifecycle.platform.health
        report = await reporter.liveness()
        body = {
            "status": _status_text(report.status),
            "message": report.message,
        }
        return JSONResponse(content=body, status_code=200)

    @app.get("/version")
    async def version():
        return {
            "version": __version__,
            "name": "eaip-platform",
        }

    # Register all routers under the /api prefix (matching the frontend API URL)
    # WebSocket stays at the root so the wsUrl remains ws://host/ws.
    app.include_router(auth.router, prefix="/api")
    app.include_router(brains.router, prefix="/api")
    app.include_router(copilot.router, prefix="/api")
    app.include_router(investigations.router, prefix="/api")
    app.include_router(orchestrations.router, prefix="/api")
    app.include_router(tour.router, prefix="/api")
    app.include_router(agents.router, prefix="/api")
    app.include_router(governance.router, prefix="/api")
    app.include_router(workflows.router, prefix="/api")
    app.include_router(knowledge.router, prefix="/api")
    app.include_router(kgraph.router, prefix="/api")
    app.include_router(missions.router, prefix="/api")
    app.include_router(runtime.router, prefix="/api")
    app.include_router(events_router.router, prefix="/api")
    app.include_router(organizations.router, prefix="/api")
    app.include_router(deployments.router, prefix="/api")
    app.include_router(websocket.router)
    app.include_router(workflow_versions.router, prefix="/api")
    app.include_router(pulse.router)
    app.include_router(decisions.router)
    app.include_router(recommendations.router)
    app.include_router(workflow_designer.router, prefix="/api")
    app.include_router(mission_analytics.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")
    app.include_router(monitoring_routes.router, prefix="/api")
    app.include_router(search_router.router, prefix="/api")
    app.include_router(search_persistence.router, prefix="/api")
    app.include_router(workforce.router, prefix="/api")
    app.include_router(marketplace_routes.router, prefix="/api")
    app.include_router(notifications_router.router, prefix="/api")
    app.include_router(operations_analytics.router, prefix="/api")
    app.include_router(cost_intelligence.router, prefix="/api")
    app.include_router(reports.router, prefix="/api")
    app.include_router(administration_center.router, prefix="/api")
    app.include_router(memory.router, prefix="/api")
    app.include_router(workspaces.router, prefix="/api")
    app.include_router(workflow_export.router, prefix="/api")
    app.include_router(system_routes.router, prefix="/api")
    app.include_router(goals.router, prefix="/api")
    app.include_router(automation.router, prefix="/api")

    log.info("http.routes_registered", count=len(app.routes))

    return app
