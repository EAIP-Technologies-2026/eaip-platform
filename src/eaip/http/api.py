from __future__ import annotations

import time

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from eaip._version import __version__
from eaip.app.lifecycle import ApplicationLifecycle
from eaip.health.checks import HealthStatus
from eaip.health.reporter import HealthReporter
from eaip.http.routers import (
    admin,
    agents,
    auth,
    deployments,
    events_router,
    knowledge,
    marketplace_routes,
    memory,
    mission_analytics,
    missions,
    monitoring,
    monitoring_routes,
    notifications_router,
    organizations,
    runtime,
    search_router,
    websocket,
    workflow_designer,
    workflow_versions,
    workflows,
)
from eaip.logging.context import get_logger

log = get_logger("eaip.http.api")


def create_app(lifecycle: ApplicationLifecycle) -> FastAPI:
    app = FastAPI(
        title="EAIP Platform",
        version=__version__,
        lifespan=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
                infra_checks = [{
                    "component": "infrastructure",
                    "status": infra_report.status.value,
                    "message": infra_report.message,
                    "details": infra_report.details,
                }]
            except Exception:
                pass

        bg_tasks = []
        if lifecycle._infrastructure:
            bg_tasks = lifecycle._infrastructure.background_tasks.status()

        healthy = report.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
        body = {
            "status": report.status.value if hasattr(report.status, "value") else str(report.status),
            "message": report.message,
            "checks": [
                {
                    "component": c.component,
                    "status": c.status.value if hasattr(c.status, "value") else str(c.status),
                    "message": c.message,
                }
                for c in report.children
            ] + infra_checks,
            "background_tasks": bg_tasks,
        }
        status_code = 200 if healthy else 503
        return JSONResponse(content=body, status_code=status_code)

    @app.get("/ready")
    async def ready():
        return {"status": "ready"}

    @app.get("/live")
    async def live():
        return {"status": "alive"}

    @app.get("/version")
    async def version():
        return {
            "version": __version__,
            "name": "eaip-platform",
        }

    # Register all routers
    app.include_router(auth.router)
    app.include_router(agents.router)
    app.include_router(workflows.router)
    app.include_router(knowledge.router)
    app.include_router(missions.router)
    app.include_router(runtime.router)
    app.include_router(events_router.router)
    app.include_router(monitoring.router)
    app.include_router(organizations.router)
    app.include_router(deployments.router)
    app.include_router(websocket.router)
    app.include_router(workflow_versions.router)
    app.include_router(workflow_designer.router)
    app.include_router(mission_analytics.router)
    app.include_router(admin.router)
    app.include_router(monitoring_routes.router)
    app.include_router(search_router.router)
    app.include_router(marketplace_routes.router)
    app.include_router(notifications_router.router)
    app.include_router(memory.router)

    log.info("http.routes_registered", count=len(app.routes))

    return app
