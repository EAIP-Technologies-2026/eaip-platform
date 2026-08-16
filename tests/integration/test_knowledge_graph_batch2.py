"""Batch 2 — Platform Knowledge Graph & Topology Traversal Integration & Security Tests."""

from __future__ import annotations

from typing import Any, cast

import pytest

from eaip.admin.audit import AuditLogger
from eaip.capabilities.inventory import load_canonical_inventory
from eaip.context.permission_context import IdentityScope
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.copilot.action_executor import GovernedActionExecutor
from eaip.copilot.approvals import ApprovalService
from eaip.copilot.enterprise_assistant import EnterpriseAssistantService
from eaip.copilot.governance import GovernancePolicy
from eaip.copilot.intelligence import AssistantIntelligenceService
from eaip.copilot.memory import GovernedMemoryService
from eaip.copilot.operational_intelligence import OperationalIntelligenceService
from eaip.copilot.role_context import (
    ActiveEntityContext,
    RoleAwareContextBuilder,
)
from eaip.copilot.tour.fixtures import TourFixtureService
from eaip.copilot.tour.service import TourService
from eaip.kgraph.platform_graph import (
    PlatformKnowledgeService,
    PlatformNodeType,
    build_platform_knowledge_graph,
)
from eaip.memory.engine import MemoryEngine
from eaip.memory.store import InMemoryStore
from eaip.policy.authorization import AuthorizationManager
from eaip.policy.engine import PolicyEngine
from eaip.policy.registry import PolicyRegistry


class MockExecuteTool:
    name = "mock_ops_tool"
    description = "Mock ops tool."

    async def execute(self, **kwargs: object) -> str:
        return '{"result": "success", "executed": true}'


@pytest.fixture
async def batch2_env() -> dict[str, Any]:
    """Build the authoritative environment with KnowledgeGraph for Batch 2."""
    cap_registry = load_canonical_inventory()
    policy_engine = PolicyEngine()
    policy_registry = PolicyRegistry()
    authz_manager = AuthorizationManager(policy_engine, policy_registry)
    resolver = PermissionContextResolver(authz_manager, cap_registry)
    kg = await build_platform_knowledge_graph(cap_registry)
    kg_service = PlatformKnowledgeService(kg)
    audit = AuditLogger()
    approvals = ApprovalService()
    governance = GovernancePolicy()
    mem_engine = MemoryEngine(InMemoryStore())
    memory_service = GovernedMemoryService(
        engine=mem_engine, governance=governance, audit=audit
    )

    grounded = AssistantIntelligenceService(cap_registry, resolver, kg_service)
    operational = OperationalIntelligenceService(audit_logger=audit)
    tour_service = TourService(
        governance=governance,
        audit=audit,
        fixture_service=TourFixtureService(audit=audit),
        memory_service=memory_service,
    )
    executor = GovernedActionExecutor(
        tools={"mock_ops_tool": cast(Any, MockExecuteTool())},
        authz_manager=authz_manager,
        capability_registry=cap_registry,
        permission_resolver=resolver,
        approvals=approvals,
        audit=audit,
    )
    context_builder = RoleAwareContextBuilder(
        capability_registry=cap_registry,
        permission_resolver=resolver,
        knowledge_service=kg_service,
        operational_intelligence=operational,
    )
    assistant = EnterpriseAssistantService(
        capability_registry=cap_registry,
        permission_resolver=resolver,
        context_builder=context_builder,
        grounded_intelligence=grounded,
        operational_intelligence=operational,
        tour_service=tour_service,
        action_executor=executor,
        memory_service=memory_service,
        knowledge_service=kg_service,
    )

    return {
        "assistant": assistant,
        "context_builder": context_builder,
        "kg_service": kg_service,
        "resolver": resolver,
        "registry": cap_registry,
    }


ADMIN_USER = {
    "user_id": "usr-admin-01",
    "tenant_id": "tenant-corp",
    "organization_id": "org-core",
    "roles": ["admin"],
    "teams": ["secops", "platform"],
}

OPERATOR_USER = {
    "user_id": "usr-op-01",
    "tenant_id": "tenant-corp",
    "organization_id": "org-ops",
    "roles": ["operator"],
    "teams": ["ops"],
}

VIEWER_USER = {
    "user_id": "usr-view-01",
    "tenant_id": "tenant-corp",
    "organization_id": "org-view",
    "roles": ["viewer"],
    "teams": ["viewers"],
}


# ============================================================================ #
# 1. Topology Queries & Permission Scoping
# ============================================================================ #


@pytest.mark.asyncio
async def test_capability_topology_authorized_admin(batch2_env: dict[str, Any]) -> None:
    kg_service: PlatformKnowledgeService = batch2_env["kg_service"]
    resolver: PermissionContextResolver = batch2_env["resolver"]

    identity = IdentityScope(user_id="admin-1", tenant_id="tenant-corp", roles=("admin",))
    perm_ctx = resolver.resolve_context(identity)

    topo = await kg_service.get_capability_topology("eaip.agents", context=perm_ctx)
    assert "error" not in topo
    assert topo["capability"].id == "cap:eaip.agents"
    assert len(topo["services"]) > 0
    assert len(topo["apis"]) > 0
    assert len(topo["events"]) > 0
    assert len(topo["routes"]) > 0


@pytest.mark.asyncio
async def test_capability_topology_restricted_capability_filtered(
    batch2_env: dict[str, Any],
) -> None:
    kg_service: PlatformKnowledgeService = batch2_env["kg_service"]
    resolver: PermissionContextResolver = batch2_env["resolver"]

    # Operator cannot see eaip.administration
    identity = IdentityScope(user_id="op-1", tenant_id="tenant-corp", roles=("operator",))
    perm_ctx = resolver.resolve_context(identity)

    topo = await kg_service.get_capability_topology("eaip.administration", context=perm_ctx)
    assert "error" in topo
    assert "restricted" in topo["error"].lower()


@pytest.mark.asyncio
async def test_connected_node_anti_leakage(batch2_env: dict[str, Any]) -> None:
    """If capability A connects to restricted capability B, B must not appear in dependencies."""
    kg_service: PlatformKnowledgeService = batch2_env["kg_service"]
    resolver: PermissionContextResolver = batch2_env["resolver"]

    identity = IdentityScope(user_id="op-1", tenant_id="tenant-corp", roles=("operator",))
    perm_ctx = resolver.resolve_context(identity)

    topo = await kg_service.get_capability_topology("eaip.dashboard", context=perm_ctx)
    assert "error" not in topo

    # Check that no restricted capability is in dependencies
    dep_cap_names = [
        getattr(d, "properties", {}).get("capability_name") or d.id.removeprefix("cap:")
        for d in topo["dependencies"]
    ]
    for dep_name in dep_cap_names:
        assert perm_ctx.can_see(dep_name), (
            f"Restricted capability {dep_name} leaked in topology!"
        )


# ============================================================================ #
# 2. Dependency & Dependent Traversal
# ============================================================================ #


@pytest.mark.asyncio
async def test_dependencies_and_dependents(batch2_env: dict[str, Any]) -> None:
    kg_service: PlatformKnowledgeService = batch2_env["kg_service"]
    resolver: PermissionContextResolver = batch2_env["resolver"]

    identity = IdentityScope(user_id="admin-1", tenant_id="tenant-corp", roles=("admin",))
    perm_ctx = resolver.resolve_context(identity)

    deps = await kg_service.get_dependencies("eaip.agents", context=perm_ctx)
    assert len(deps) > 0

    dependents = await kg_service.get_dependents("eaip.agents", context=perm_ctx)
    assert isinstance(dependents, list)


@pytest.mark.asyncio
async def test_category_helpers(batch2_env: dict[str, Any]) -> None:
    kg_service: PlatformKnowledgeService = batch2_env["kg_service"]
    resolver: PermissionContextResolver = batch2_env["resolver"]

    identity = IdentityScope(user_id="admin-1", tenant_id="tenant-corp", roles=("admin",))
    perm_ctx = resolver.resolve_context(identity)

    services = await kg_service.get_related_services("eaip.agents", context=perm_ctx)
    assert len(services) > 0
    assert any(s.type == PlatformNodeType.SERVICE for s in services)

    apis = await kg_service.get_related_apis("eaip.agents", context=perm_ctx)
    assert len(apis) > 0
    assert any(a.type == PlatformNodeType.API for a in apis)

    events = await kg_service.get_related_events("eaip.agents", context=perm_ctx)
    assert len(events) > 0
    assert any(e.type == PlatformNodeType.EVENT for e in events)

    docs = await kg_service.get_related_documentation("eaip.agents", context=perm_ctx)
    assert len(docs) > 0
    assert any(d.type == PlatformNodeType.DOCUMENTATION for d in docs)


@pytest.mark.asyncio
async def test_path_finding_bounded(batch2_env: dict[str, Any]) -> None:
    kg_service: PlatformKnowledgeService = batch2_env["kg_service"]
    resolver: PermissionContextResolver = batch2_env["resolver"]

    identity = IdentityScope(user_id="admin-1", tenant_id="tenant-corp", roles=("admin",))
    perm_ctx = resolver.resolve_context(identity)

    path = await kg_service.find_path("eaip.agents", "eaip.workflows", context=perm_ctx)
    assert isinstance(path, list)
    assert len(path) > 0
    assert path[0] == "cap:eaip.agents"
    assert path[-1] == "cap:eaip.workflows"


# ============================================================================ #
# 3. Active Entity + Graph Grounding
# ============================================================================ #


@pytest.mark.asyncio
async def test_active_entity_topology_grounding(batch2_env: dict[str, Any]) -> None:
    assistant: EnterpriseAssistantService = batch2_env["assistant"]

    entity_ctx = ActiveEntityContext(
        entity_id="ag-data-pipeline",
        entity_type="agent",
        active_tab="topology",
    )

    # Contextual question with pronoun "this agent"
    resp = await assistant.answer(
        "What services does this agent use?",
        ADMIN_USER,
        current_route="/agents/ag-data-pipeline",
        entity_context=entity_ctx,
    )

    assert "Services powering" in resp.reply
    assert resp.grounded_capability == "eaip.agents"


@pytest.mark.asyncio
async def test_active_entity_what_is_connected_to_this(batch2_env: dict[str, Any]) -> None:
    assistant: EnterpriseAssistantService = batch2_env["assistant"]

    entity_ctx = ActiveEntityContext(
        entity_id="wf-nightly-sync",
        entity_type="workflow",
        active_tab="overview",
    )

    resp = await assistant.answer(
        "What is connected to this?",
        ADMIN_USER,
        current_route="/workflows/wf-nightly-sync",
        entity_context=entity_ctx,
    )

    assert "Systems connected to" in resp.reply
    assert resp.grounded_capability == "eaip.workflows"


@pytest.mark.asyncio
async def test_active_entity_impact_analysis(batch2_env: dict[str, Any]) -> None:
    assistant: EnterpriseAssistantService = batch2_env["assistant"]

    resp = await assistant.answer(
        "What could be affected if Workflows changes?",
        ADMIN_USER,
        current_route="/workflows",
    )

    assert "dependencies" in resp.reply.lower() or "impact" in resp.reply.lower()


# ============================================================================ #
# 4. Assistant Self-Knowledge & Anti-Hallucination
# ============================================================================ #


@pytest.mark.asyncio
async def test_assistant_architecture_overview(batch2_env: dict[str, Any]) -> None:
    assistant: EnterpriseAssistantService = batch2_env["assistant"]

    resp = await assistant.answer(
        "What is EAIP's architecture?",
        ADMIN_USER,
        current_route="/",
    )

    assert "EAIP Platform Architecture Overview" in resp.reply
    assert "Autonomous Agents" in resp.reply
    assert "Policy Engine" in resp.reply


@pytest.mark.asyncio
async def test_assistant_apis_query(batch2_env: dict[str, Any]) -> None:
    assistant: EnterpriseAssistantService = batch2_env["assistant"]

    resp = await assistant.answer(
        "Which API powers Agents?",
        ADMIN_USER,
        current_route="/agents",
    )

    assert "APIs exposing" in resp.reply
    assert "/api/v1/agents" in resp.reply


@pytest.mark.asyncio
async def test_assistant_events_query(batch2_env: dict[str, Any]) -> None:
    assistant: EnterpriseAssistantService = batch2_env["assistant"]

    resp = await assistant.answer(
        "What events does Agents emit?",
        ADMIN_USER,
        current_route="/agents",
    )

    assert "Domain events emitted by" in resp.reply
    assert "Agent" in resp.reply


@pytest.mark.asyncio
async def test_assistant_documentation_query(batch2_env: dict[str, Any]) -> None:
    assistant: EnterpriseAssistantService = batch2_env["assistant"]

    resp = await assistant.answer(
        "What documentation explains Agents?",
        ADMIN_USER,
        current_route="/agents",
    )

    assert "Documentation for" in resp.reply


@pytest.mark.asyncio
async def test_assistant_connection_path_query(batch2_env: dict[str, Any]) -> None:
    assistant: EnterpriseAssistantService = batch2_env["assistant"]

    resp = await assistant.answer(
        "How does Agents connect to Workflows?",
        ADMIN_USER,
        current_route="/",
    )

    assert "Connection between" in resp.reply
    assert "cap:eaip.agents" in resp.reply
    assert "cap:eaip.workflows" in resp.reply


@pytest.mark.asyncio
async def test_restricted_capability_topology_refusal(batch2_env: dict[str, Any]) -> None:
    assistant: EnterpriseAssistantService = batch2_env["assistant"]

    # Operator asking about restricted administration topology
    resp = await assistant.answer(
        "What is connected to Administration?",
        OPERATOR_USER,
        current_route="/",
    )

    assert "restricted" in resp.reply.lower()
    assert "cap:eaip.administration" not in resp.sources
