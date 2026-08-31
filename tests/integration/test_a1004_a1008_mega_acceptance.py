"""End-to-End Mega Acceptance Test Suite for A1004-A1008.

Validates the full enterprise intelligence operating system:
A1001 (Capability Registry)
  -> A1002 (Permission-Aware Context)
  -> A1003 (Platform Knowledge Graph)
  -> A1004 (Assistant Intelligence)
  -> A1005 (Governed Action Execution)
  -> A1006 (Dynamic Guided Tour)
  -> A1007 (Operational Intelligence)
  -> A1008 (Full Platform Acceptance)
"""

from __future__ import annotations

import pytest

from eaip.admin.audit import AuditLogger
from eaip.agents.registry import AgentRegistry
from eaip.capabilities.capability import OperationType
from eaip.capabilities.inventory import load_canonical_inventory
from eaip.context.permission_context import IdentityScope
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.copilot.action_executor import GovernedActionExecutor
from eaip.copilot.approvals import ApprovalService
from eaip.copilot.intelligence import AssistantIntelligenceService
from eaip.copilot.models import RiskTier
from eaip.copilot.operational_intelligence import OperationalIntelligenceService
from eaip.copilot.tour.steps import get_dynamic_tour_steps
from eaip.kgraph.platform_graph import (
    PlatformKnowledgeService,
    build_platform_knowledge_graph,
)
from eaip.policy.authorization import AuthorizationManager
from eaip.policy.engine import PolicyEngine
from eaip.policy.registry import PolicyRegistry
from eaip.workflow.registry import WorkflowRegistry


class MockExecuteTool:
    name = "mock_ops_tool"
    description = "Mock ops tool."

    async def execute(self, **kwargs: object) -> str:
        return '{"result": "success", "executed": true}'


@pytest.fixture
async def platform_environment() -> dict:
    cap_registry = load_canonical_inventory()
    policy_engine = PolicyEngine()
    policy_registry = PolicyRegistry()
    authz_manager = AuthorizationManager(policy_engine, policy_registry)
    resolver = PermissionContextResolver(authz_manager, cap_registry)
    kg = await build_platform_knowledge_graph(cap_registry)
    kg_service = PlatformKnowledgeService(kg)
    approvals = ApprovalService()
    audit = AuditLogger()
    agents = AgentRegistry()
    workflows = WorkflowRegistry()

    tools = {"mock_ops_tool": MockExecuteTool()}

    assistant_intel = AssistantIntelligenceService(
        capability_registry=cap_registry,
        permission_resolver=resolver,
        knowledge_service=kg_service,
    )

    action_executor = GovernedActionExecutor(
        tools=tools,
        authz_manager=authz_manager,
        capability_registry=cap_registry,
        permission_resolver=resolver,
        approvals=approvals,
        audit=audit,
    )

    op_intel = OperationalIntelligenceService(
        audit_logger=audit,
        agent_registry=agents,
        workflow_registry=workflows,
    )

    return {
        "capabilities": cap_registry,
        "policy_registry": policy_registry,
        "resolver": resolver,
        "kg_service": kg_service,
        "approvals": approvals,
        "audit": audit,
        "assistant_intel": assistant_intel,
        "action_executor": action_executor,
        "op_intel": op_intel,
    }


@pytest.mark.asyncio
async def test_assistant_role_aware_intelligence(platform_environment: dict) -> None:
    """A1004 & A1008: Verify role-aware grounded answers and anti-hallucination."""
    intel: AssistantIntelligenceService = platform_environment["assistant_intel"]

    # 1. Admin querying administration
    admin_user = {"user_id": "admin-1", "tenant_id": "tenant-1", "roles": ["admin"]}
    admin_resp = await intel.answer_grounded_query(
        "Tell me about Platform Administration", admin_user
    )
    assert admin_resp.grounded_capability == "eaip.administration"
    assert "Platform Administration" in admin_resp.reply
    assert len(admin_resp.sources) > 0

    # 2. Operator querying administration -> restricted visibility notice
    op_user = {"user_id": "op-1", "tenant_id": "tenant-1", "roles": ["operator"]}
    op_resp = await intel.answer_grounded_query("Tell me about Platform Administration", op_user)
    assert "restricted from viewing its details" in op_resp.reply

    # 3. Current page intelligence on /knowledge
    curr_resp = await intel.answer_grounded_query(
        "What is this page?", op_user, current_route="/knowledge"
    )
    assert curr_resp.grounded_capability == "eaip.knowledge"
    assert "Knowledge Base" in curr_resp.reply

    # 4. Anti-hallucination check
    halluc_resp = await intel.answer_grounded_query(
        "Explain the Quantum Teleportation Hub", admin_user
    )
    assert halluc_resp.is_uncertain is True
    assert halluc_resp.confidence == 0.0
    assert "don't have sufficient platform evidence" in halluc_resp.reply


@pytest.mark.asyncio
async def test_governed_action_execution_pipeline(platform_environment: dict) -> None:
    """A1005 & A1008: Verify authorization recheck, approvals, and audit trail."""
    executor: GovernedActionExecutor = platform_environment["action_executor"]
    audit: AuditLogger = platform_environment["audit"]

    # Operator planning destructive workflow cancellation
    op_user = {"user_id": "op-1", "tenant_id": "tenant-1", "roles": ["operator"]}
    plan = await executor.plan_action(
        intent="Cancel active workflow",
        user=op_user,
        capability_name="eaip.workflows",
        operation=OperationType.CANCEL,
        tool_name="mock_ops_tool",
    )
    assert plan.risk_tier is RiskTier.DESTRUCTIVE
    assert plan.requires_approval is True

    # 1. Unapproved attempt halts
    unapproved = await executor.execute_action(plan, op_user, approved=False)
    assert unapproved.status == "approval_required"
    assert unapproved.approval_id is not None

    # 2. Approved execution succeeds and logs audit
    approved = await executor.execute_action(plan, op_user, approved=True)
    assert approved.status == "executed"
    assert approved.audit_entry_id is not None
    assert len(audit._store) >= 2


@pytest.mark.asyncio
async def test_cross_tenant_security_enforcement(platform_environment: dict) -> None:
    """A1005 & A1008: Verify cross-tenant execution is rejected at runtime."""
    executor: GovernedActionExecutor = platform_environment["action_executor"]
    user_alpha = {"user_id": "user-1", "tenant_id": "tenant-alpha", "roles": ["operator"]}

    plan = await executor.plan_action(
        intent="Run ops on beta",
        user={"user_id": "user-1", "tenant_id": "tenant-beta", "roles": ["operator"]},
        capability_name="eaip.operations",
        operation=OperationType.EXECUTE,
        tool_name="mock_ops_tool",
    )

    result = await executor.execute_action(plan, user_alpha)
    assert result.status == "denied"
    assert "Cross-tenant" in result.summary


@pytest.mark.asyncio
async def test_dynamic_tour_permission_filtering(platform_environment: dict) -> None:
    """A1006 & A1008: Verify dynamic tour filters restricted capabilities and aligns start route."""
    resolver: PermissionContextResolver = platform_environment["resolver"]

    op_identity = IdentityScope(user_id="op-1", tenant_id="tenant-1", roles=("operator",))
    op_ctx = resolver.resolve_context(op_identity)

    # Tour starting on /knowledge for operator
    steps = get_dynamic_tour_steps(context=op_ctx, start_route="/knowledge")
    step_ids = [s.id for s in steps]

    assert "administration" not in step_ids
    assert steps[0].id == "knowledge"
    assert steps[0].route == "/knowledge"
    assert steps[0].order == 0


@pytest.mark.asyncio
async def test_operational_intelligence_live_telemetry(platform_environment: dict) -> None:
    """A1007 & A1008: Verify operational intelligence answers live state with freshness markers."""
    op_intel: OperationalIntelligenceService = platform_environment["op_intel"]
    identity = IdentityScope(user_id="sre-1", tenant_id="tenant-1", roles=("operator",))

    resp = await op_intel.answer_operational_query("What is our platform health?", identity)
    assert "Live Operational Telemetry" in resp.reply
    assert "System Health Status" in resp.reply
    assert "Live data captured at" in resp.reply
    assert resp.tenant_id == "tenant-1"
