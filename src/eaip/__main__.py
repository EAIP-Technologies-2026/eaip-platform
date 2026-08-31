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

    # Memory services — wire persistent PostgreSQL-backed store with fallback
    from eaip.memory.engine import MemoryEngine
    from eaip.memory.sql_store import SqlMemoryStore
    from eaip.memory.store import InMemoryStore

    try:
        memory_store = SqlMemoryStore()
        _mem_engine = MemoryEngine(memory_store)
        log.info("memory.store.sql_backed")
    except Exception as exc:
        _mem_engine = MemoryEngine(InMemoryStore())
        log.warning("memory.store.fallback_in_memory", error=str(exc))
    memory_engine = _mem_engine
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

    # Knowledge services — Qdrant-backed vector store with graceful fallback
    from eaip.knowledge.embedding import MockEmbeddingProvider
    from eaip.knowledge.engine import KnowledgeEngine
    from eaip.knowledge.in_memory_store import InMemoryVectorStore
    from eaip.knowledge.qdrant_store import QdrantStore
    from eaip.knowledge.registry import KnowledgeRegistry as KR

    knowledge_registry = KR()
    try:
        knowledge_vector_store = QdrantStore(
            host=os.environ.get("QDRANT_HOST", "localhost"),
            port=int(os.environ.get("QDRANT_PORT", "6333")),
            api_key=os.environ.get("QDRANT_API_KEY", ""),
        )
        log.info("knowledge.store.qdrant")
    except Exception as exc:
        knowledge_vector_store = InMemoryVectorStore()
        log.warning("knowledge.store.fallback_in_memory", error=str(exc))

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

    def _brain_event_publisher(event):
        if _asyncio_loop and not _asyncio_loop.is_closed():
            try:
                asyncio.ensure_future(events.publish(event), loop=_asyncio_loop)
            except Exception:
                pass

    container.register_instance(
        EnterpriseBrain,
        EnterpriseBrain(
            knowledge_engine=knowledge_engine,
            memory_engine=memory_engine,
            event_publisher=_brain_event_publisher,
        ),
    )

    # Knowledge Graph — wire the existing platform knowledge graph with
    # the GraphIndex and SemanticRelationshipService for traversal.
    from eaip.kgraph.graph import KnowledgeGraph
    from eaip.kgraph.index import GraphIndex
    from eaip.kgraph.integration import GraphRuntimeModule
    from eaip.kgraph.semantic import SemanticRelationshipService

    knowledge_graph = KnowledgeGraph()
    graph_index = GraphIndex(knowledge_graph)
    semantic_relationships = SemanticRelationshipService(knowledge_graph)
    container.register_instance(KnowledgeGraph, knowledge_graph)
    container.register_instance(GraphIndex, graph_index)
    container.register_instance(SemanticRelationshipService, semantic_relationships)

    graph_module = GraphRuntimeModule(graph=knowledge_graph)
    container.register_instance(GraphRuntimeModule, graph_module)

    # Semantic Indexing — wire the existing service for document embedding
    from eaip.semantic_indexing.integration import SemanticIndexingRuntimeModule

    semantic_indexing_module = SemanticIndexingRuntimeModule()
    container.register_instance(SemanticIndexingRuntimeModule, semantic_indexing_module)

    # Knowledge Permissions — wire the existing permission service
    from eaip.knowledge_permissions.integration import KnowledgePermissionRuntimeModule

    knowledge_permissions_module = KnowledgePermissionRuntimeModule()
    container.register_instance(
        KnowledgePermissionRuntimeModule, knowledge_permissions_module
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

    # Intelligence Pulse & Decision Intelligence (B07)
    from eaip.pulse.integration import PulseRuntimeModule
    from eaip.decisions.integration import DecisionRuntimeModule
    from eaip.recommendations.integration import RecommendationRuntimeModule

    pulse_module = PulseRuntimeModule()
    pulse_module.register(container)
    container.register_instance(PulseRuntimeModule, pulse_module)

    decisions_module = DecisionRuntimeModule()
    decisions_module.register(container)
    container.register_instance(DecisionRuntimeModule, decisions_module)

    recommendations_module = RecommendationRuntimeModule()
    recommendations_module.register(container)
    container.register_instance(RecommendationRuntimeModule, recommendations_module)

    # Governance and Compliance Services (B08)
    from eaip.policy.integration import PolicyRuntimeModule
    from eaip.guardrails.integration import GuardrailRuntimeModule
    from eaip.ai_governance.integration import AiGovernanceRuntimeModule
    from eaip.agent_governance.integration import AgentGovernanceRuntimeModule
    from eaip.compliance.integration import ComplianceRuntimeModule

    policy_module = PolicyRuntimeModule()
    guardrails_module = GuardrailRuntimeModule()
    ai_governance_module = AiGovernanceRuntimeModule()
    agent_governance_module = AgentGovernanceRuntimeModule()
    compliance_module = ComplianceRuntimeModule()

    container.register_instance(PolicyRuntimeModule, policy_module)
    container.register_instance(GuardrailRuntimeModule, guardrails_module)
    container.register_instance(AiGovernanceRuntimeModule, ai_governance_module)
    container.register_instance(AgentGovernanceRuntimeModule, agent_governance_module)
    container.register_instance(ComplianceRuntimeModule, compliance_module)

    # Observability and Cost Services (B09)
    from eaip.observability.integration import ObservabilityRuntimeModule
    from eaip.ai_observability.integration import AiObservabilityRuntimeModule
    from eaip.cost.integration import CostRuntimeModule
    from eaip.costalloc.integration import CostAllocRuntimeModule
    from eaip.metering.integration import MeteringRuntimeModule

    obs_module = ObservabilityRuntimeModule()
    ai_obs_module = AiObservabilityRuntimeModule()
    cost_module = CostRuntimeModule()
    costalloc_module = CostAllocRuntimeModule()
    metering_module = MeteringRuntimeModule()

    container.register_instance(ObservabilityRuntimeModule, obs_module)
    container.register_instance(AiObservabilityRuntimeModule, ai_obs_module)
    container.register_instance(CostRuntimeModule, cost_module)
    container.register_instance(CostAllocRuntimeModule, costalloc_module)
    container.register_instance(MeteringRuntimeModule, metering_module)

    # Health & Operations Services (B11)
    from eaip.healthagg.integration import HealthAggRuntimeModule
    from eaip.healthrpt.integration import HealthRptRuntimeModule
    from eaip.diagnostics.integration import DiagnosticsRuntimeModule
    from eaip.operations.integration import OperationsRuntimeModule

    healthagg_module = HealthAggRuntimeModule()
    healthrpt_module = HealthRptRuntimeModule()
    diagnostics_module = DiagnosticsRuntimeModule()
    operations_module = OperationsRuntimeModule()

    container.register_instance(HealthAggRuntimeModule, healthagg_module)
    container.register_instance(HealthRptRuntimeModule, healthrpt_module)
    container.register_instance(DiagnosticsRuntimeModule, diagnostics_module)
    container.register_instance(OperationsRuntimeModule, operations_module)

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

    # Scheduling / Workforce analytics / Simulation — must be before Conductor so tools can reference them
    from eaip.scheduling.repository import ScheduleExecutionRepository, ScheduleRepository
    from eaip.scheduling.service import SchedulingService

    _sched_repo = ScheduleRepository()
    _sched_exec_repo = ScheduleExecutionRepository()
    _scheduling_service = SchedulingService(
        repo=_sched_repo,
        exec_repo=_sched_exec_repo,
        event_bus=events,
        workflow_engine=wf_engine,
        mission_registry=mission_registry,
        agent_runtime=agent_runtime,
    )
    container.register_instance(ScheduleRepository, _sched_repo)
    container.register_instance(ScheduleExecutionRepository, _sched_exec_repo)
    container.register_instance(SchedulingService, _scheduling_service)

    from eaip.workforce.analytics import WorkforceAnalyticsService

    _workforce_analytics = WorkforceAnalyticsService(
        registry=workforce_module.registry,
        orchestrator=workforce_module.orchestrator,
        event_bus=events,
    )
    container.register_instance(WorkforceAnalyticsService, _workforce_analytics)

    from eaip.simulation.engine import SimulationEngine

    _simulation_engine = SimulationEngine(event_bus=events, knowledge_graph=knowledge_graph, seed=42)
    container.register_instance(SimulationEngine, _simulation_engine)

    # MCP / Connector Fabric — Batch 1
    from eaip.mcp.credentials import CredentialStore
    from eaip.mcp.discovery import MCPDiscoveryService
    from eaip.mcp.executor import MCPToolExecutor
    from eaip.mcp.registry import MCPServerRegistry, MCPToolRegistry
    from eaip.mcp.synthetic import MockTransport, create_synthetic_servers, create_synthetic_tools
    from eaip.solution_packs.registry import SolutionPackRegistry
    from eaip.onboarding.service import OnboardingService

    _mcp_servers = MCPServerRegistry()
    _mcp_tools = MCPToolRegistry()
    _mcp_credentials = CredentialStore()
    _mcp_executor = MCPToolExecutor(server_registry=_mcp_servers, tool_registry=_mcp_tools, event_bus=events)
    _mcp_discovery = MCPDiscoveryService(server_registry=_mcp_servers, tool_registry=_mcp_tools, event_bus=events)
    container.register_instance(MCPServerRegistry, _mcp_servers)
    container.register_instance(MCPToolRegistry, _mcp_tools)
    container.register_instance(CredentialStore, _mcp_credentials)
    container.register_instance(MCPToolExecutor, _mcp_executor)
    container.register_instance(MCPDiscoveryService, _mcp_discovery)
    _pack_registry = SolutionPackRegistry()
    container.register_instance(SolutionPackRegistry, _pack_registry)
    _onboarding_svc = OnboardingService(solution_registry=_pack_registry, event_bus=events)
    container.register_instance(OnboardingService, _onboarding_svc)

    from eaip.swarm.engine import SwarmEngine
    from eaip.long_missions.service import LongMissionService
    from eaip.runtime_registry.registry import RuntimeRegistry
    from eaip.runtime_registry.models import RuntimeRecord, RuntimeKind
    from eaip.audit_chain.chain import AuditChain
    from eaip.federation.service import FederationService
    from eaip.intelligence.registry import CapabilityRegistry
    from eaip.intelligence.kernel import IntelligenceKernel
    from eaip.intelligence.supervision import SupervisionEngine
    from eaip.intelligence.cognition import CognitiveEngine
    from eaip.intelligence.decision_service import DecisionIntelligenceService
    from eaip.intelligence.coordination import CoordinationEngine
    from eaip.intelligence.memory_consistency import MemoryConsistencyEngine

    _swarm_engine = SwarmEngine(agent_runtime=agent_runtime, event_bus=events)
    container.register_instance(SwarmEngine, _swarm_engine)
    _long_mission_svc = LongMissionService(event_bus=events)
    container.register_instance(LongMissionService, _long_mission_svc)
    _runtime_registry = RuntimeRegistry()
    _runtime_registry.register(RuntimeRecord(runtime_id="local-1", kind=RuntimeKind.local_runtime, name="Local Runtime", capabilities=("agents", "workflows"), status="healthy", tenant_id="default"))
    container.register_instance(RuntimeRegistry, _runtime_registry)
    _audit_chain = AuditChain()
    container.register_instance(AuditChain, _audit_chain)
    _federation_svc = FederationService()
    container.register_instance(FederationService, _federation_svc)
    _cap_registry = CapabilityRegistry()
    for _cat, _name in [("agent", "Agent Execution"), ("workflow", "Workflow Execution"), ("knowledge", "Knowledge Search"), ("decision", "Decision Analysis")]:
        from eaip.intelligence.models import CapabilityRecord
        _cap_registry.register(CapabilityRecord(capability_id=f"cap-{_cat}", name=_name, category=_cat, tenant_id="default"))
    container.register_instance(CapabilityRegistry, _cap_registry)
    _intel_kernel = IntelligenceKernel(registry=_cap_registry, agent_runtime=agent_runtime, event_bus=events)
    container.register_instance(IntelligenceKernel, _intel_kernel)
    container.register_instance(SupervisionEngine, SupervisionEngine(event_bus=events))
    container.register_instance(CognitiveEngine, CognitiveEngine(knowledge_engine=knowledge_engine, memory_engine=memory_engine, event_bus=events))
    container.register_instance(DecisionIntelligenceService, DecisionIntelligenceService(simulation_engine=_simulation_engine, event_bus=events))
    container.register_instance(CoordinationEngine, CoordinationEngine(workforce_analytics=_workforce_analytics, event_bus=events))
    container.register_instance(MemoryConsistencyEngine, MemoryConsistencyEngine())
    # M7 — Marketplace + Deployment Ecosystem
    from eaip.deployment_packs.registry import ArtifactRegistry, DeploymentConfigRegistry, DeploymentPackRegistry, OnboardingRegistry, SandboxRegistry
    container.register_instance(ArtifactRegistry, ArtifactRegistry())
    container.register_instance(DeploymentPackRegistry, DeploymentPackRegistry())
    container.register_instance(SandboxRegistry, SandboxRegistry())
    container.register_instance(DeploymentConfigRegistry, DeploymentConfigRegistry())
    container.register_instance(OnboardingRegistry, OnboardingRegistry())
    # M8 — Scale + Production Operations
    from eaip.scale_ops.registry import DataResidencyRegistry, DisasterRecoveryRegistry, IncidentRegistry, PoolRegistry, RegionRegistry, WorkloadScheduler
    container.register_instance(PoolRegistry, PoolRegistry())
    container.register_instance(WorkloadScheduler, WorkloadScheduler())
    container.register_instance(RegionRegistry, RegionRegistry())
    container.register_instance(DataResidencyRegistry, DataResidencyRegistry())
    container.register_instance(IncidentRegistry, IncidentRegistry())
    container.register_instance(DisasterRecoveryRegistry, DisasterRecoveryRegistry())
    # M9 — Executive OS + Departments
    from eaip.executive_os.registry import BriefingService, DepartmentRegistry, KPIRegistry
    container.register_instance(BriefingService, BriefingService())
    container.register_instance(DepartmentRegistry, DepartmentRegistry())
    container.register_instance(KPIRegistry, KPIRegistry())
    # M10 — Autonomous Enterprise Loop
    from eaip.enterprise_loop.engine import EnterpriseLoopEngine, ObjectiveLoopEngine, StrategicCorrectionEngine
    container.register_instance(EnterpriseLoopEngine, EnterpriseLoopEngine(event_bus=events))
    container.register_instance(ObjectiveLoopEngine, ObjectiveLoopEngine())
    container.register_instance(StrategicCorrectionEngine, StrategicCorrectionEngine())
    for _rec in create_synthetic_servers():
        _mcp_servers.register(_rec)
        transport = MockTransport(_rec.server_id, _rec.tenant_id)
        _mcp_executor.register_transport(_rec.server_id, _rec.tenant_id, transport)
        _mcp_discovery.register_transport(_rec.server_id, _rec.tenant_id, transport)
    from collections import defaultdict as _dd
    grouped: dict[tuple[str, str], list] = _dd(list)
    for _t in create_synthetic_tools():
        grouped[(_t.tenant_id, _t.server_id)].append(_t)
    for (_tid, _sid), _tools_list in grouped.items():
        _mcp_tools.discover(_sid, _tid, _tools_list)

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
        scheduling_service=_scheduling_service,
        workforce_analytics=_workforce_analytics,
        marketplace_registry=marketplace_registry,
        simulation_engine=_simulation_engine,
        mcp_server_registry=_mcp_servers,
        mcp_executor=_mcp_executor,
        agent_runtime=agent_runtime,
        workflow_engine=wf_engine,
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

    # B1 — Enterprise Assistant DI wiring: compose the fully-implemented
    # role-aware assistant stack from EXISTING authoritative services only.
    from eaip.copilot.action_executor import GovernedActionExecutor
    from eaip.copilot.enterprise_assistant import EnterpriseAssistantService
    from eaip.copilot.intelligence import AssistantIntelligenceService
    from eaip.copilot.operational_intelligence import OperationalIntelligenceService
    from eaip.copilot.role_context import RoleAwareContextBuilder
    from eaip.capabilities.registry import CapabilityRegistry as AssistantCapabilityRegistry
    from eaip.context.permission_resolver import PermissionContextResolver
    from eaip.kgraph.platform_graph import PlatformKnowledgeService
    from eaip.policy.authorization import AuthorizationManager
    from eaip.policy.engine import PolicyEngine as AuthzPolicyEngine
    from eaip.policy.registry import PolicyRegistry

    _authz_policy_registry = PolicyRegistry()
    _authz_policy_engine = AuthzPolicyEngine()
    _assistant_authz_manager = AuthorizationManager(
        engine=_authz_policy_engine,
        registry=_authz_policy_registry,
        event_bus=events,
    )
    _assistant_capability_registry = AssistantCapabilityRegistry()
    _assistant_permission_resolver = PermissionContextResolver(
        authz_manager=_assistant_authz_manager,
        capability_registry=_assistant_capability_registry,
    )
    _platform_knowledge = PlatformKnowledgeService(graph=knowledge_graph)
    _assistant_intelligence = AssistantIntelligenceService(
        capability_registry=_assistant_capability_registry,
        permission_resolver=_assistant_permission_resolver,
        knowledge_service=_platform_knowledge,
    )
    _operational_intelligence = OperationalIntelligenceService(
        health_reporter=lifecycle.platform.health,
        agent_registry=agent_registry,
        workflow_registry=wf_registry,
        audit_logger=audit_logger,
    )
    _role_context_builder = RoleAwareContextBuilder(
        capability_registry=_assistant_capability_registry,
        permission_resolver=_assistant_permission_resolver,
        knowledge_service=_platform_knowledge,
        operational_intelligence=_operational_intelligence,
    )
    _governed_action_executor = GovernedActionExecutor(
        tools=tool_registry,
        authz_manager=_assistant_authz_manager,
        capability_registry=_assistant_capability_registry,
        permission_resolver=_assistant_permission_resolver,
        approvals=approval_service,
        audit=audit_logger,
    )
    _enterprise_assistant = EnterpriseAssistantService(
        capability_registry=_assistant_capability_registry,
        permission_resolver=_assistant_permission_resolver,
        context_builder=_role_context_builder,
        grounded_intelligence=_assistant_intelligence,
        operational_intelligence=_operational_intelligence,
        tour_service=tour_service,
        action_executor=_governed_action_executor,
        memory_service=memory_service,
        knowledge_service=_platform_knowledge,
    )
    container.register_instance(AuthorizationManager, _assistant_authz_manager)
    # NOTE: AssistantCapabilityRegistry intentionally NOT registered under its
    # class name — it collides with the intelligence CapabilityRegistry binding.
    # It is composed into the services below, which are the access points.
    container.register_instance(PermissionContextResolver, _assistant_permission_resolver)
    container.register_instance(PlatformKnowledgeService, _platform_knowledge)
    container.register_instance(AssistantIntelligenceService, _assistant_intelligence)
    container.register_instance(OperationalIntelligenceService, _operational_intelligence)
    container.register_instance(RoleAwareContextBuilder, _role_context_builder)
    container.register_instance(GovernedActionExecutor, _governed_action_executor)
    container.register_instance(EnterpriseAssistantService, _enterprise_assistant)

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

    http_port = int(os.environ.get("EAIP_HTTP_PORT", "8080"))

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=http_port,
        log_level="info",
        ws="auto",
    )
    server = uvicorn.Server(config)

    log.info("http.server.starting", host="0.0.0.0", port=http_port)

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
