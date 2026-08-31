from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager

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
    digital_workforce,
    document_intelligence,
    enterprise_flows,
    events_router,
    goals,
    governance,
    governance2,
    improvement_router,
    integrations,
    methodologies,
    onboarding,
    ops_intelligence_router,
    simulation2,
    wave2_pipeline_router,
    solution_packs,
    swarms,
    long_missions,
    runtimes,
    audit_chain,
    federation,
    autonomy,
    workflow_compose,
    marketplace_trusted,
    external_integrations,
    control_plane,
    observability,
    evaluation,
    cost_v2,
    resilience,
    health_center,
    data_governance,
    provider_routing,
    config_center,
    approval_center,
    kpi,
    feature_flags,
    usage,
    deployment,
    m1_memory_knowledge,
    m2_intelligence,
    m3_reliability,
    m4_strategy,
    m5_learning_audit,
    m6_connectors_models,
    m7_marketplace,
    m7_deployment,
    m8_scale_ops,
    m9_executive,
    m10_loop,
    intelligence,
    investigations,
    kgraph,
    storyline,
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
    scheduling,
    search_persistence,
    search_router,
    simulation,
    system_routes,
    tour,
    websocket,
    workflow_designer,
    workflow_export,
    workflow_versions,
    workflows,
    workforce,
    workforce_analytics,
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
    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        try:
            from eaip.http.routers import m2_intelligence

            await m2_intelligence.hydrate_from_db()
        except Exception as exc:
            log.warning("http.m2_hydrate_failed", error=repr(exc))
        yield

    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=__version__,
        contact=API_CONTACT,
        license_info=API_LICENSE,
        lifespan=_lifespan,
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
    app.include_router(storyline.router, prefix="/api")
    app.include_router(missions.router, prefix="/api")
    app.include_router(runtime.router, prefix="/api")
    app.include_router(events_router.router, prefix="/api")
    app.include_router(organizations.router, prefix="/api")
    app.include_router(deployments.router, prefix="/api")
    app.include_router(websocket.router)
    app.include_router(workflow_versions.router, prefix="/api")
    app.include_router(pulse.router, prefix="/api")
    app.include_router(decisions.router, prefix="/api")
    app.include_router(recommendations.router, prefix="/api")
    app.include_router(workflow_designer.router, prefix="/api")
    app.include_router(mission_analytics.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")
    app.include_router(monitoring_routes.router, prefix="/api")
    app.include_router(search_router.router, prefix="/api")
    app.include_router(search_persistence.router, prefix="/api")
    app.include_router(workforce.router, prefix="/api")
    app.include_router(workforce_analytics.router, prefix="/api")
    app.include_router(scheduling.router, prefix="/api")
    app.include_router(simulation.router, prefix="/api")
    app.include_router(enterprise_flows.router, prefix="/api")
    app.include_router(integrations.router, prefix="/api")
    app.include_router(solution_packs.router, prefix="/api")
    app.include_router(onboarding.router, prefix="/api")
    app.include_router(swarms.router, prefix="/api")
    app.include_router(long_missions.router, prefix="/api")
    app.include_router(runtimes.router, prefix="/api")
    app.include_router(audit_chain.router, prefix="/api")
    app.include_router(federation.router, prefix="/api")
    app.include_router(intelligence.router, prefix="/api")
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
    app.include_router(digital_workforce.router, prefix="/api")
    app.include_router(document_intelligence.router, prefix="/api")
    app.include_router(methodologies.router, prefix="/api")
    app.include_router(governance2.router, prefix="/api")
    app.include_router(simulation2.router, prefix="/api")
    app.include_router(ops_intelligence_router.router, prefix="/api")
    app.include_router(improvement_router.router, prefix="/api")
    app.include_router(wave2_pipeline_router.router, prefix="/api")
    app.include_router(autonomy.router, prefix="/api")
    app.include_router(workflow_compose.router, prefix="/api")
    app.include_router(marketplace_trusted.router, prefix="/api")
    app.include_router(external_integrations.router, prefix="/api")
    app.include_router(control_plane.router, prefix="/api")
    app.include_router(observability.router, prefix="/api")
    app.include_router(evaluation.router, prefix="/api")
    app.include_router(cost_v2.router, prefix="/api")
    app.include_router(resilience.router, prefix="/api")
    app.include_router(health_center.router, prefix="/api")
    app.include_router(data_governance.router, prefix="/api")
    app.include_router(provider_routing.router, prefix="/api")
    app.include_router(config_center.router, prefix="/api")
    app.include_router(approval_center.router, prefix="/api")
    app.include_router(kpi.router, prefix="/api")
    app.include_router(feature_flags.router, prefix="/api")
    app.include_router(usage.router, prefix="/api")
    app.include_router(deployment.router, prefix="/api")
    app.include_router(m1_memory_knowledge.router, prefix="/api")
    app.include_router(m2_intelligence.router, prefix="/api")
    app.include_router(m3_reliability.router, prefix="/api")
    app.include_router(m4_strategy.router, prefix="/api")
    app.include_router(m5_learning_audit.router, prefix="/api")
    app.include_router(m6_connectors_models.router, prefix="/api")
    app.include_router(m7_marketplace.router, prefix="/api")
    app.include_router(m7_deployment.router, prefix="/api")
    app.include_router(m8_scale_ops.router, prefix="/api")
    app.include_router(m9_executive.router, prefix="/api")
    app.include_router(m10_loop.router, prefix="/api")

    log.info("http.routes_registered", count=len(app.routes))

    return app
