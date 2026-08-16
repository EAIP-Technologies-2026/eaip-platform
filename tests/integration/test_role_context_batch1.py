"""Batch 1 — Deep Context & Entity Grounding tests."""

from __future__ import annotations

from typing import Any, cast

import pytest

from eaip.admin.audit import AuditLogger
from eaip.capabilities.inventory import load_canonical_inventory
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
    RoleAwareAssistantContext,
    RoleAwareContextBuilder,
)
from eaip.copilot.tour.fixtures import TourFixtureService
from eaip.copilot.tour.service import TourService
from eaip.kgraph.platform_graph import (
    PlatformKnowledgeService,
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
async def assistant_env() -> dict[str, Any]:
    """Build the full authoritative Batch 1 composition for tests."""
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


# ============================================================================ #
# Batch 1 Tests: ActiveEntityContext and Context Enrichment
# ============================================================================ #


@pytest.mark.asyncio
async def test_batch1_active_entity_context_explicit(assistant_env: dict[str, Any]) -> None:
    builder: RoleAwareContextBuilder = assistant_env["context_builder"]

    entity_ctx = ActiveEntityContext(
        entity_id="ag-customer-01",
        entity_type="agent",
        active_tab="metrics",
        selected_ids=("ag-customer-01",),
        page_context={"status": "healthy", "uptime_pct": 99.9},
    )

    ctx = await builder.build(
        ADMIN_USER,
        current_route="/agents",
        entity_context=entity_ctx,
    )

    assert isinstance(ctx, RoleAwareAssistantContext)
    assert ctx.active_entity.entity_id == "ag-customer-01"
    assert ctx.active_entity.entity_type == "agent"
    assert ctx.active_entity.active_tab == "metrics"
    assert ctx.active_entity.selected_ids == ("ag-customer-01",)
    assert ctx.active_entity.page_context.get("status") == "healthy"


@pytest.mark.asyncio
async def test_batch1_active_entity_context_route_inference(assistant_env: dict[str, Any]) -> None:
    builder: RoleAwareContextBuilder = assistant_env["context_builder"]

    # Route /agents/ag-sentiment-02 should infer agent type and id
    ctx1 = await builder.build(
        ADMIN_USER,
        current_route="/agents/ag-sentiment-02",
    )
    assert ctx1.active_entity.entity_type == "agent"
    assert ctx1.active_entity.entity_id == "ag-sentiment-02"

    # Route /workflows/wf-nightly-etl should infer workflow type and id
    ctx2 = await builder.build(
        ADMIN_USER,
        current_route="/workflows/wf-nightly-etl",
    )
    assert ctx2.active_entity.entity_type == "workflow"
    assert ctx2.active_entity.entity_id == "wf-nightly-etl"

    # Route /brains/brain-financial should infer brain type and id
    ctx3 = await builder.build(
        ADMIN_USER,
        current_route="/brains/brain-financial",
    )
    assert ctx3.active_entity.entity_type == "brain"
    assert ctx3.active_entity.entity_id == "brain-financial"


@pytest.mark.asyncio
async def test_batch1_assistant_contextual_action_resolution(
    assistant_env: dict[str, Any],
) -> None:
    assistant: EnterpriseAssistantService = assistant_env["assistant"]

    entity_ctx = ActiveEntityContext(
        entity_id="ag-billing-01",
        entity_type="agent",
        active_tab="overview",
    )

    # When query uses contextual pronoun "restart this agent"
    resp = await assistant.answer(
        "restart this agent",
        ADMIN_USER,
        current_route="/agents/ag-billing-01",
        entity_context=entity_ctx,
    )

    assert resp.grounded_capability is not None
    assert "agents" in resp.grounded_capability.lower()
    assert "action plan prepared" in resp.reply.lower()


@pytest.mark.asyncio
async def test_batch1_dict_entity_context_compat(assistant_env: dict[str, Any]) -> None:
    builder: RoleAwareContextBuilder = assistant_env["context_builder"]

    ctx = await builder.build(
        ADMIN_USER,
        current_route="/",
        entity_context={
            "entity_id": "wf-123",
            "entity_type": "workflow",
            "active_tab": "runs",
            "selected_ids": ["wf-123"],
        },
    )

    assert ctx.active_entity.entity_id == "wf-123"
    assert ctx.active_entity.entity_type == "workflow"
    assert ctx.active_entity.active_tab == "runs"
    assert ctx.active_entity.selected_ids == ("wf-123",)
