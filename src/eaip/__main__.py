from __future__ import annotations

import asyncio
import os
import sys

import uvicorn
from dotenv import load_dotenv

from eaip._version import __version__
from eaip.app.builder import ApplicationBuilder
from eaip.http.api import create_app
from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.health import DatabaseHealthCheck
from eaip.logging.context import get_logger

_asyncio_loop: asyncio.AbstractEventLoop | None = None


async def _async_main() -> None:
    global _asyncio_loop
    _asyncio_loop = asyncio.get_running_loop()

    log = get_logger("eaip.__main__")

    builder = ApplicationBuilder()
    lifecycle = builder.build()

    await lifecycle.start()

    container = lifecycle.platform.container
    events = lifecycle.platform.events
    metrics_meter = container.try_resolve("Meter")  # noqa: F841

    # ------------------------------------------------------------------
    # Register core service instances into the DI container
    # ------------------------------------------------------------------

    # Agent services
    from eaip.agents.registry import AgentRegistry
    from eaip.agents.runtime import AgentRuntime

    agent_registry = AgentRegistry(event_bus=events)
    container.register_instance(AgentRegistry, agent_registry)

    from eaip.adapters.llm.stub import StubLLMAdapter
    from eaip.tools.builtin.current_time import CurrentTimeTool
    from eaip.tools.builtin.echo import EchoTool
    from eaip.tools.registry import ToolRegistry

    tool_registry = ToolRegistry()
    tool_registry.register(EchoTool())
    tool_registry.register(CurrentTimeTool())
    container.register_instance(ToolRegistry, tool_registry)

    llm_adapter = StubLLMAdapter()
    agent_runtime = AgentRuntime(
        llm_adapter=llm_adapter,
        tool_registry=tool_registry,
        event_bus=events,
    )
    container.register_instance(AgentRuntime, agent_runtime)

    # Auth services
    from eaip.auth.auth_providers import AuthenticationService

    auth_secret = os.environ.get("EAIP_AUTH_SECRET")
    if not auth_secret:
        auth_secret = os.environ.get("EAIP_AUTH__SECRET")
    if not auth_secret:
        raise RuntimeError(
            "EAIP_AUTH_SECRET is required. Set a strong random secret via environment variable."
        )
    auth_service = AuthenticationService(
        secret=auth_secret,
        event_bus=events,
    )
    container.register_instance(AuthenticationService, auth_service)

    # Workflow services
    from eaip.workflow.executor import WorkflowEngine
    from eaip.workflow.registry import WorkflowRegistry

    wf_registry = WorkflowRegistry(event_bus=events)
    container.register_instance(WorkflowRegistry, wf_registry)

    wf_engine = WorkflowEngine(event_bus=events)
    container.register_instance(WorkflowEngine, wf_engine)

    # Memory services
    from eaip.memory.engine import MemoryEngine
    from eaip.memory.store import InMemoryStore

    memory_engine = MemoryEngine(InMemoryStore())
    container.register_instance(MemoryEngine, memory_engine)

    # Sentry integration
    from eaip.integrations.sentry import SentryHealthCheck

    sentry_health = SentryHealthCheck()
    if lifecycle.platform.settings.sentry.dsn:
        sentry_health.mark_healthy()

    # Mission services
    from eaip.runtime.mission import MissionRegistry

    mission_registry = MissionRegistry(
        event_bus=events,
        agent_runtime=agent_runtime,
        workflow_registry=wf_registry,
        workflow_engine=wf_engine,
    )
    container.register_instance(MissionRegistry, mission_registry)

    # WebSocket services
    from eaip.ws.channel_manager import ChannelManager
    from eaip.ws.connection_manager import ConnectionManager
    from eaip.ws.push_service import PushService

    conn_mgr = ConnectionManager()
    channel_mgr = ChannelManager()
    push_svc = PushService(channel_manager=channel_mgr, connection_manager=conn_mgr)
    container.register_instance(ConnectionManager, conn_mgr)
    container.register_instance(ChannelManager, channel_mgr)
    container.register_instance(PushService, push_svc)

    # Workspace services
    from eaip.session.workspace import WorkspaceManager

    workspace_manager = WorkspaceManager(event_bus=events)
    container.register_instance(WorkspaceManager, workspace_manager)

    # Knowledge services
    from eaip.knowledge.embedding import MockEmbeddingProvider
    from eaip.knowledge.engine import KnowledgeEngine
    from eaip.knowledge.in_memory_store import InMemoryVectorStore
    from eaip.knowledge.registry import KnowledgeRegistry as KR

    knowledge_registry = KR()
    knowledge_vector_store = InMemoryVectorStore()

    async def _publish_event(event):
        if _asyncio_loop and not _asyncio_loop.is_closed():
            try:
                await events.publish(event)
            except Exception:
                pass

    knowledge_engine = KnowledgeEngine(
        knowledge_registry,
        knowledge_vector_store,
        MockEmbeddingProvider(),
        event_publisher=_publish_event,
    )
    container.register_instance(KR, knowledge_registry)
    container.register_instance(KnowledgeEngine, knowledge_engine)

    # Enterprise search — wire the existing EnterpriseSearchEngine with the
    # existing KnowledgeSearchProvider over the shared retrieval stack.
    from eaip.knowledge.retrieval_engine import RetrievalEngine
    from eaip.search.engine import EnterpriseSearchEngine
    from eaip.search.providers import KnowledgeSearchProvider

    retrieval_engine = RetrievalEngine(
        vector_store=knowledge_vector_store,
        embedding_provider=MockEmbeddingProvider(),
    )
    container.register_instance(RetrievalEngine, retrieval_engine)

    search_engine = EnterpriseSearchEngine()
    search_engine.register_provider(
        KnowledgeSearchProvider(retrieval_engine=retrieval_engine)
    )
    container.register_instance(EnterpriseSearchEngine, search_engine)

    # Event store for activity feed
    from eaip.events.event import DomainEvent
    from eaip.events.store import EventStore
    from eaip.brain.enterprise_brain import EnterpriseBrain

    event_store = EventStore(maxlen=1000)
    container.register_instance(EventStore, event_store)
    container.register_instance(
        EnterpriseBrain,
        EnterpriseBrain(
            knowledge_engine=knowledge_engine,
            memory_engine=memory_engine,
            event_publisher=lambda event: None,
        ),
    )

    # Reporting — surface the existing ExportEngine in the DI container so the
    # /reports router can run and track export jobs.
    from eaip.export.engine import ExportEngine

    export_engine = ExportEngine()
    container.register_instance(ExportEngine, export_engine)

    # Marketplace — register the existing marketplace services so the
    # /marketplace router browses, publishes, and installs real packages.
    from eaip.marketplace.registry import MarketplaceRegistry
    from eaip.marketplace.discovery import DiscoveryService
    from eaip.marketplace.manager import PackageManager
    from eaip.marketplace.publisher import Publisher

    marketplace_registry = MarketplaceRegistry()
    container.register_instance(MarketplaceRegistry, marketplace_registry)
    container.register_instance(DiscoveryService, DiscoveryService(registry=marketplace_registry))
    container.register_instance(
        PackageManager, PackageManager(registry=marketplace_registry)
    )
    container.register_instance(Publisher, Publisher(registry=marketplace_registry))

    async def _record_event(event: DomainEvent) -> None:
        await event_store.record(event)

    events.subscribe(DomainEvent, _record_event, include_subclasses=True)

    # Workforce services
    from eaip.workforce.integration import WorkforceRuntimeModule

    workforce_module = WorkforceRuntimeModule(
        agent_runtime=agent_runtime,
        workflow_engine=wf_engine,
        event_bus=events,
    )
    container.register_instance(WorkforceRuntimeModule, workforce_module)
    container.register_instance(workforce_module.registry.__class__, workforce_module.registry)
    container.register_instance(
        workforce_module.orchestrator.__class__, workforce_module.orchestrator
    )

    # Admin services
    from eaip.admin.audit import AuditLogger
    from eaip.admin.manager import RuntimeManager
    from eaip.copilot.governance import GovernancePolicy
    from eaip.copilot.memory import GovernedMemoryService
    from eaip.enterprise_settings.service import EnterpriseSettingsService
    from eaip.license.manager import LicenseManager

    audit_logger = AuditLogger(event_bus=events)
    container.register_instance(AuditLogger, audit_logger)
    memory_service = GovernedMemoryService(
        engine=memory_engine,
        governance=GovernancePolicy(),
        audit=audit_logger,
    )
    container.register_instance(GovernedMemoryService, memory_service)

    # Copilot services — EAIP Conductor (governed assistant)
    from eaip.copilot.approvals import ApprovalService
    from eaip.copilot.planner import ConductorPlanner
    from eaip.copilot.service import ConductorService
    from eaip.copilot.tools import build_copilot_tools

    copilot_tools = build_copilot_tools(
        health_reporter=lifecycle.platform.health,
        agent_registry=agent_registry,
        workflow_registry=wf_registry,
        knowledge_engine=knowledge_engine,
        memory_service=memory_service,
    )
    for tool in copilot_tools.values():
        if tool_registry.try_get(tool.name) is None:
            tool_registry.register(tool)
        else:
            # Conductor's governed wrapper replaces a builtin of the same name
            # (e.g. current_time) so the governed tool set stays authoritative.
            tool_registry.unregister(tool.name)
            tool_registry.register(tool)

    approval_service = ApprovalService(event_bus=events)
    container.register_instance(ApprovalService, approval_service)

    conductor_service = ConductorService(
        tool_registry=tool_registry,
        planner=ConductorPlanner(copilot_tools),
        governance=GovernancePolicy(),
        approvals=approval_service,
        audit=audit_logger,
        event_bus=events,
    )
    container.register_instance(ConductorService, conductor_service)

    # Tour services — EAIP Conductor Phase 8 Guided Tour
    from eaip.copilot.tour.fixtures import TourFixtureService
    from eaip.copilot.tour.service import TourService

    tour_fixture_service = TourFixtureService(audit=audit_logger)
    container.register_instance(TourFixtureService, tour_fixture_service)
    tour_service = TourService(
        governance=GovernancePolicy(),
        audit=audit_logger,
        fixture_service=tour_fixture_service,
        memory_service=memory_service,
    )
    container.register_instance(TourService, tour_service)

    # Investigation services — EAIP Conductor Phase 9
    from eaip.copilot.investigation.service import InvestigationService
    from eaip.copilot.investigation.tools import build_investigation_tools

    investigation_service = InvestigationService(
        governance=GovernancePolicy(),
        audit=audit_logger,
        memory_service=memory_service,
        event_bus=events,
    )
    container.register_instance(InvestigationService, investigation_service)

    investigation_tools = build_investigation_tools(
        investigation_service=investigation_service,
        health_reporter=lifecycle.platform.health,
        agent_registry=agent_registry,
        workflow_registry=wf_registry,
        knowledge_engine=knowledge_engine,
    )
    for tool in investigation_tools.values():
        if tool_registry.try_get(tool.name) is None:
            tool_registry.register(tool)

    # Orchestration services — EAIP Conductor Phase 10
    from eaip.copilot.orchestration.service import OrchestrationService
    from eaip.copilot.orchestration.tools import build_orchestration_tools

    orchestration_service = OrchestrationService(
        governance=GovernancePolicy(),
        audit=audit_logger,
        tool_registry=tool_registry,
        event_bus=events,
    )
    container.register_instance(OrchestrationService, orchestration_service)

    orchestration_tools = build_orchestration_tools(
        orchestration_service=orchestration_service,
    )
    for tool in orchestration_tools.values():
        if tool_registry.try_get(tool.name) is None:
            tool_registry.register(tool)

    # Register core health checks
    from eaip.health.checks import (
        DependencyClass,
        HealthReport,
        HealthStatus,
    )

    class _AgentRuntimeHealthCheck:
        name = "eaip.agents.runtime"
        criticality = DependencyClass.CRITICAL
        configured = True

        async def check(self) -> HealthReport:
            return HealthReport(
                component="AgentRuntime",
                status=HealthStatus.HEALTHY,
                details={
                    "runs": len(agent_runtime._runs) if hasattr(agent_runtime, "_runs") else 0
                },
            )

    class _WorkflowEngineHealthCheck:
        name = "eaip.workflow.engine"
        criticality = DependencyClass.CRITICAL
        configured = True

        async def check(self) -> HealthReport:
            return HealthReport(component="WorkflowEngine", status=HealthStatus.HEALTHY)

    class _KnowledgeEngineHealthCheck:
        name = "eaip.knowledge.engine"
        criticality = DependencyClass.CRITICAL
        configured = True

        async def check(self) -> HealthReport:
            return HealthReport(component="KnowledgeEngine", status=HealthStatus.HEALTHY)

    class _MemoryEngineHealthCheck:
        name = "eaip.memory.engine"
        criticality = DependencyClass.CRITICAL
        configured = True

        async def check(self) -> HealthReport:
            return HealthReport(
                component="MemoryEngine",
                status=HealthStatus.HEALTHY,
                details={"stores": ["in_memory"]},
            )

    health_reporter = lifecycle.platform.health
    health_reporter.register(_AgentRuntimeHealthCheck())
    health_reporter.register(_WorkflowEngineHealthCheck())
    health_reporter.register(_KnowledgeEngineHealthCheck())
    health_reporter.register(_MemoryEngineHealthCheck())

    # Database health check
    db_provider_name = lifecycle.platform.settings.database_provider.provider
    db_health_check = DatabaseHealthCheck(
        provider_name=db_provider_name,
        db_health_fn=DatabaseConnection.health,
    )
    health_reporter.register(db_health_check)
    health_reporter.register(sentry_health)

    kernel = lifecycle.kernel
    if kernel is not None:
        runtime_mgr = RuntimeManager(kernel=kernel, event_bus=events)
        container.register_instance(RuntimeManager, runtime_mgr)
        await workforce_module.start(kernel)

    license_mgr = LicenseManager(
        event_callback=lambda e: (
            asyncio.ensure_future(events.publish(e)) if hasattr(events, "publish") else None
        )
    )
    container.register_instance(LicenseManager, license_mgr)

    settings_svc = EnterpriseSettingsService()
    container.register_instance(EnterpriseSettingsService, settings_svc)

    log.info("services.registered", count=len(container._providers))

    # ------------------------------------------------------------------

    app = create_app(lifecycle)

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        ws="auto",
    )
    server = uvicorn.Server(config)

    log.info("http.server.starting", host="0.0.0.0", port=8080)

    try:
        await server.serve()
    finally:
        await lifecycle.stop()


def main() -> None:
    load_dotenv()
    if "--version" in sys.argv or "-V" in sys.argv:
        print(f"eaip {__version__}")
        sys.exit(0)
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
