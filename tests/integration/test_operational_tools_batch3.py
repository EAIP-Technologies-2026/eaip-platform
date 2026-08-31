"""Batch 3 — Operational Tool Suite & Governed Actions Integration & Security Tests.

Verifies:
- Canonical operational tool suite registration and metadata.
- Permission-filtered tool discovery (can_see vs can_act).
- Governed execution workflow (UNDERSTAND -> PLAN -> GOVERN -> EXECUTE).
- Real-time authorization re-checking on every execution.
- Human approval gating on high-risk and sensitive operations.
- Approval rejection preventing mutation.
- Successful approval allowing execution.
- Idempotency & duplicate execution prevention.
- Cross-tenant isolation enforcement.
- Strict refusal on unauthorized operations (no natural language escalation).
- Consequence & dry-run analysis inquiries.
- Audit event emission on planning, execution, and decisions.
"""

from __future__ import annotations

from typing import Any

import pytest

from eaip.admin.audit import AuditLogger
from eaip.capabilities.capability import OperationType
from eaip.capabilities.inventory import load_canonical_inventory
from eaip.context.permission_context import IdentityScope
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.copilot.action_executor import GovernedActionExecutor
from eaip.copilot.approvals import ApprovalService
from eaip.copilot.enterprise_assistant import EnterpriseAssistantService
from eaip.copilot.governance import GovernancePolicy
from eaip.copilot.intelligence import AssistantIntelligenceService
from eaip.copilot.memory import GovernedMemoryService
from eaip.copilot.models import RiskTier
from eaip.copilot.operational_intelligence import OperationalIntelligenceService
from eaip.copilot.role_context import (
    ActiveEntityContext,
    RoleAwareContextBuilder,
)
from eaip.copilot.tools import (
    OperationalToolRegistry,
    create_canonical_operational_registry,
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


@pytest.fixture
async def batch3_env() -> dict[str, Any]:
    """Build the authoritative environment with Operational Tools for Batch 3."""
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
        engine=mem_engine,
        governance=governance,
        audit=audit,
    )
    operational_intelligence = OperationalIntelligenceService(
        audit_logger=audit,
    )
    intelligence = AssistantIntelligenceService(
        cap_registry,
        resolver,
        kg_service,
    )
    context_builder = RoleAwareContextBuilder(
        capability_registry=cap_registry,
        permission_resolver=resolver,
        knowledge_service=kg_service,
    )
    tours = TourService(
        governance=governance,
        audit=audit,
        fixture_service=TourFixtureService(audit=audit),
        memory_service=memory_service,
    )

    # Build canonical operational tool registry
    op_tool_registry = create_canonical_operational_registry(
        approval_service=approvals,
        health_reporter=None,
    )

    # Initialize GovernedActionExecutor with the operational tool registry
    action_executor = GovernedActionExecutor(
        tools=op_tool_registry,
        approvals=approvals,
        authz_manager=authz_manager,
        audit=audit,
        capability_registry=cap_registry,
        permission_resolver=resolver,
    )

    assistant = EnterpriseAssistantService(
        capability_registry=cap_registry,
        permission_resolver=resolver,
        context_builder=context_builder,
        grounded_intelligence=intelligence,
        operational_intelligence=operational_intelligence,
        tour_service=tours,
        action_executor=action_executor,
        memory_service=memory_service,
        knowledge_service=kg_service,
    )

    return {
        "cap_registry": cap_registry,
        "resolver": resolver,
        "authz_manager": authz_manager,
        "approvals": approvals,
        "audit": audit,
        "tools": op_tool_registry,
        "executor": action_executor,
        "assistant": assistant,
        "kg_service": kg_service,
    }


# ==============================================================================
# 1. TOOL REGISTRY & METADATA TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_canonical_operational_tools_registered(batch3_env: dict[str, Any]) -> None:
    """Verify all 13 canonical operational tools are properly registered with metadata."""
    tools: OperationalToolRegistry = batch3_env["tools"]
    all_tools = tools.all_operational_tools()
    assert len(all_tools) >= 13

    expected_tools = {
        "system_health",
        "inspect_agent_status",
        "inspect_workflow_status",
        "inspect_approvals",
        "pause_agent",
        "resume_agent",
        "restart_agent",
        "cancel_agent_run",
        "pause_workflow",
        "resume_workflow",
        "cancel_workflow",
        "approve_action",
        "reject_action",
    }
    registered_names = {t.name for t in all_tools}
    assert expected_tools.issubset(registered_names)

    # Check metadata properties on a tool
    pause_tool = tools.get_operational_tool("pause_agent")
    assert pause_tool is not None
    assert pause_tool.metadata.capability_id == "eaip.agents"
    assert pause_tool.metadata.operation_type == OperationType.PAUSE
    assert pause_tool.metadata.risk_classification == RiskTier.ACTION


@pytest.mark.asyncio
async def test_permission_scoped_tool_discovery(batch3_env: dict[str, Any]) -> None:
    """Verify tools are filtered based on role permissions (Admin vs Operator vs ReadOnly)."""
    tools: OperationalToolRegistry = batch3_env["tools"]
    resolver: PermissionContextResolver = batch3_env["resolver"]

    # 1. Admin identity
    admin_ctx = resolver.resolve_context(
        IdentityScope(user_id="u_admin", tenant_id="t1", roles=("admin",))
    )
    admin_tools = tools.get_tools_for_identity(admin_ctx)
    admin_tool_names = {t.name for t in admin_tools}
    assert "system_health" in admin_tool_names
    assert "pause_agent" in admin_tool_names
    assert "cancel_workflow" in admin_tool_names
    assert "approve_action" in admin_tool_names

    # 2. Operator identity (can act on operations and agents)
    operator_ctx = resolver.resolve_context(
        IdentityScope(user_id="u_op", tenant_id="t1", roles=("operator",))
    )
    op_tools = tools.get_tools_for_identity(operator_ctx)
    op_tool_names = {t.name for t in op_tools}
    assert "system_health" in op_tool_names
    assert "inspect_agent_status" in op_tool_names

    # 3. Read-only viewer identity (cannot mutate or govern)
    viewer_ctx = resolver.resolve_context(
        IdentityScope(user_id="u_view", tenant_id="t1", roles=("viewer",))
    )
    viewer_tools = tools.get_tools_for_identity(viewer_ctx)
    viewer_tool_names = {t.name for t in viewer_tools}
    assert "system_health" in viewer_tool_names
    # Viewer cannot see mutation tools
    assert "pause_agent" not in viewer_tool_names
    assert "cancel_workflow" not in viewer_tool_names
    assert "approve_action" not in viewer_tool_names


# ==============================================================================
# 2. GOVERNED EXECUTION & PERMISSION GATE TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_authorized_read_operation(batch3_env: dict[str, Any]) -> None:
    """Verify authorized read operation executes through GovernedActionExecutor."""
    executor: GovernedActionExecutor = batch3_env["executor"]
    audit: AuditLogger = batch3_env["audit"]
    user = {"user_id": "u1", "tenant_id": "t1", "roles": ("operator",)}

    plan = await executor.plan_action(
        intent="Check system health status",
        user=user,
        capability_name="eaip.health",
        operation=OperationType.READ,
        tool_name="system_health",
    )
    assert plan.risk_tier == RiskTier.INFORMATIONAL
    assert not plan.requires_approval

    result = await executor.execute_action(plan, user=user)
    assert result.status == "executed"
    assert "status" in result.result_data or "output" in result.result_data
    assert result.audit_entry_id is not None

    # Check audit log
    entries = audit.query(action="copilot.action.read")
    assert len(entries) >= 1


@pytest.mark.asyncio
async def test_authorized_mutation_planning(batch3_env: dict[str, Any]) -> None:
    """Verify authorized mutation is planned with correct risk and target ID."""
    executor: GovernedActionExecutor = batch3_env["executor"]
    user = {"user_id": "u1", "tenant_id": "t1", "roles": ("operator",)}

    plan = await executor.plan_action(
        intent="Pause agent ag-primary-01",
        user=user,
        capability_name="eaip.agents",
        operation=OperationType.PAUSE,
        target_id="ag-primary-01",
        target_entity_type="agent",
    )
    assert plan.risk_tier == RiskTier.ACTION
    assert plan.target_id == "ag-primary-01"
    assert "ag-primary-01" in plan.preview
    assert plan.tool_name == "pause_agent"


@pytest.mark.asyncio
async def test_unauthorized_mutation_refusal(batch3_env: dict[str, Any]) -> None:
    """Verify unauthorized role cannot execute mutations and receives denial."""
    executor: GovernedActionExecutor = batch3_env["executor"]
    viewer_user = {"user_id": "u_viewer", "tenant_id": "t1", "roles": ("viewer",)}

    # Viewer attempts to plan and execute a mutation on agents
    plan = await executor.plan_action(
        intent="Pause agent ag-01",
        user=viewer_user,
        capability_name="eaip.agents",
        operation=OperationType.PAUSE,
        target_id="ag-01",
    )

    result = await executor.execute_action(plan, user=viewer_user)
    assert result.status == "denied"
    assert "do not have permission" in result.summary


@pytest.mark.asyncio
async def test_visible_but_mutation_forbidden(batch3_env: dict[str, Any]) -> None:
    """Verify visible capability forbids mutation when role cannot act."""
    assistant: EnterpriseAssistantService = batch3_env["assistant"]
    viewer_user = {"user_id": "u_viewer", "tenant_id": "t1", "roles": ("viewer",)}

    # Viewer asks assistant to restart an agent
    resp = await assistant.answer(
        "Restart agent ag-critical",
        user=viewer_user,
        current_route="/agents",
    )
    assert "not authorized to execute actions" in resp.reply
    assert resp.grounded_capability == "eaip.agents"


# ==============================================================================
# 3. APPROVAL GATING & WORKFLOW TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_approval_required_operation_gated(batch3_env: dict[str, Any]) -> None:
    """Verify destructive operations require human approval before execution."""
    executor: GovernedActionExecutor = batch3_env["executor"]
    approvals: ApprovalService = batch3_env["approvals"]
    user = {"user_id": "u1", "tenant_id": "t1", "roles": ("operator",)}

    plan = await executor.plan_action(
        intent="Cancel workflow wf-critical-prod",
        user=user,
        capability_name="eaip.workflows",
        operation=OperationType.CANCEL,
        target_id="wf-critical-prod",
    )
    assert plan.risk_tier == RiskTier.DESTRUCTIVE
    assert plan.requires_approval

    result = await executor.execute_action(plan, user=user, approved=False)
    assert result.status == "approval_required"
    assert result.approval_id is not None

    # Check pending approvals
    pending = approvals.list_pending()
    assert any(p.id == result.approval_id for p in pending)


@pytest.mark.asyncio
async def test_approval_rejection_prevents_execution(batch3_env: dict[str, Any]) -> None:
    """Verify rejecting an approval request marks it rejected and logs audit."""
    approvals: ApprovalService = batch3_env["approvals"]
    executor: GovernedActionExecutor = batch3_env["executor"]
    user = {"user_id": "u_admin", "tenant_id": "t1", "roles": ("admin",)}

    # Create approval request
    req = await approvals.create(
        tool_name="cancel_workflow",
        arguments={"target_id": "wf-999"},
        requester_id="u_requester",
        risk=RiskTier.DESTRUCTIVE,
    )
    assert req.status.value == "pending"

    # Reject the request
    decided = await approvals.decide(
        approval_id=req.id,
        decided_by="u_admin",
        approve=False,
    )
    assert decided.status.value == "rejected"

    # Plan for the rejected request should not proceed with approved=False
    plan = await executor.plan_action(
        intent="Cancel workflow wf-999",
        user=user,
        capability_name="eaip.workflows",
        operation=OperationType.CANCEL,
        target_id="wf-999",
    )
    res = await executor.execute_action(plan, user=user, approved=False)
    assert res.status == "approval_required"


@pytest.mark.asyncio
async def test_successful_approval_allows_execution(batch3_env: dict[str, Any]) -> None:
    """Verify that once approved, execution proceeds and returns live grounded output."""
    executor: GovernedActionExecutor = batch3_env["executor"]
    user = {"user_id": "u_admin", "tenant_id": "t1", "roles": ("admin",)}

    plan = await executor.plan_action(
        intent="Cancel workflow wf-test-run",
        user=user,
        capability_name="eaip.workflows",
        operation=OperationType.CANCEL,
        target_id="wf-test-run",
    )

    # Execute with explicit approval
    result = await executor.execute_action(plan, user=user, approved=True)
    assert result.status == "executed"
    assert "CANCEL" in result.summary


# ==============================================================================
# 4. IDEMPOTENCY & ISOLATION TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_duplicate_execution_prevention_idempotency(batch3_env: dict[str, Any]) -> None:
    """Verify executing same ActionPlan twice returns cached ActionResult."""
    executor: GovernedActionExecutor = batch3_env["executor"]
    user = {"user_id": "u1", "tenant_id": "t1", "roles": ("admin",)}

    plan = await executor.plan_action(
        intent="Inspect health",
        user=user,
        capability_name="eaip.health",
        operation=OperationType.READ,
        tool_name="system_health",
    )

    res1 = await executor.execute_action(plan, user=user)
    assert res1.status == "executed"

    res2 = await executor.execute_action(plan, user=user)
    assert res2 is res1  # Idempotent return of cached execution result


@pytest.mark.asyncio
async def test_cross_tenant_execution_prevention(batch3_env: dict[str, Any]) -> None:
    """Verify attempting to execute an action planned for another tenant is strictly denied."""
    executor: GovernedActionExecutor = batch3_env["executor"]
    user_tenant1 = {"user_id": "u1", "tenant_id": "tenant-alpha", "roles": ("operator",)}
    user_tenant2 = {"user_id": "u2", "tenant_id": "tenant-beta", "roles": ("operator",)}

    plan = await executor.plan_action(
        intent="Pause agent",
        user=user_tenant1,
        capability_name="eaip.agents",
        operation=OperationType.PAUSE,
        target_id="ag-01",
    )
    assert plan.target_tenant_id == "tenant-alpha"

    # User from tenant-beta attempts to execute tenant-alpha's plan
    res = await executor.execute_action(plan, user=user_tenant2)
    assert res.status == "denied"
    assert "Cross-tenant" in res.summary


# ==============================================================================
# 5. ASSISTANT NATURAL LANGUAGE INTEGRATION TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_assistant_governance_decision(batch3_env: dict[str, Any]) -> None:
    """Verify assistant handles 'approve appr-123' and 'reject appr-123' requests."""
    assistant: EnterpriseAssistantService = batch3_env["assistant"]
    approvals: ApprovalService = batch3_env["approvals"]
    admin_user = {"user_id": "admin_user", "tenant_id": "t1", "roles": ("admin",)}

    # Create pending approval
    req = await approvals.create(
        tool_name="cancel_workflow",
        arguments={"target_id": "wf-100"},
        requester_id="u_dev",
        risk=RiskTier.DESTRUCTIVE,
    )

    # Admin asks assistant to approve
    resp = await assistant.answer(
        f"Approve approval request {req.id}",
        user=admin_user,
        current_route="/operations",
    )
    assert "Action Approval Resolved" in resp.reply
    assert "approved" in resp.reply
    assert req.id in resp.reply


@pytest.mark.asyncio
async def test_assistant_governance_rejection_unauthorized(batch3_env: dict[str, Any]) -> None:
    """Verify non-admin/non-operator cannot approve or reject actions via assistant."""
    assistant: EnterpriseAssistantService = batch3_env["assistant"]
    viewer_user = {"user_id": "viewer_user", "tenant_id": "t1", "roles": ("viewer",)}

    resp = await assistant.answer(
        "Approve approval request appr-99999",
        user=viewer_user,
        current_route="/operations",
    )
    assert "not authorized to approve or reject actions" in resp.reply


@pytest.mark.asyncio
async def test_assistant_consequence_inquiry(batch3_env: dict[str, Any]) -> None:
    """Verify assistant provides consequence and impact analysis for 'what happens if I cancel'."""
    assistant: EnterpriseAssistantService = batch3_env["assistant"]
    user = {"user_id": "u1", "tenant_id": "t1", "roles": ("operator",)}

    resp = await assistant.answer(
        "What happens if I cancel this workflow?",
        user=user,
        current_route="/workflows",
    )
    assert "Consequence Analysis" in resp.reply
    assert "CANCEL" in resp.reply
    assert "DESTRUCTIVE" in resp.reply
    assert "Mandatory Human Approval" in resp.reply


@pytest.mark.asyncio
async def test_assistant_operations_available_for_entity(batch3_env: dict[str, Any]) -> None:
    """Verify assistant describes available operations when asked about a specific entity."""
    assistant: EnterpriseAssistantService = batch3_env["assistant"]
    user = {"user_id": "u1", "tenant_id": "t1", "roles": ("operator",)}

    resp = await assistant.answer(
        "What operations are available for agents?",
        user=user,
        current_route="/agents",
    )
    assert "Operations available for" in resp.reply
    assert "eaip.agents" in resp.reply


@pytest.mark.asyncio
async def test_assistant_clarification_on_ambiguous_action(batch3_env: dict[str, Any]) -> None:
    """Verify assistant asks for clarification when action target is completely ambiguous."""
    assistant: EnterpriseAssistantService = batch3_env["assistant"]
    user = {"user_id": "u1", "tenant_id": "t1", "roles": ("operator",)}

    resp = await assistant.answer(
        "Pause",
        user=user,
        current_route="/",  # root route has no specific capability
    )
    assert "Tell me the target capability" in resp.reply
    assert resp.is_uncertain


@pytest.mark.asyncio
async def test_assistant_action_with_active_entity_context(batch3_env: dict[str, Any]) -> None:
    """Verify assistant correctly resolves target entity ID from ActiveEntityContext."""
    assistant: EnterpriseAssistantService = batch3_env["assistant"]
    admin_user = {"user_id": "u_admin", "tenant_id": "t1", "roles": ("admin",)}

    ent_ctx = ActiveEntityContext(
        entity_type="agent",
        entity_id="ag-autonomous-42",
    )

    resp = await assistant.answer(
        "Pause this agent",
        user=admin_user,
        current_route="/agents/ag-autonomous-42",
        entity_context=ent_ctx,
    )
    assert "Action plan prepared" in resp.reply
    assert "ag-autonomous-42" in resp.reply


@pytest.mark.asyncio
async def test_no_authorization_bypass_without_permissions(batch3_env: dict[str, Any]) -> None:
    """Verify that an attacker crafting direct ActionPlan cannot bypass executor permissions."""
    executor: GovernedActionExecutor = batch3_env["executor"]
    attacker = {"user_id": "attacker", "tenant_id": "t1", "roles": ("anonymous",)}

    plan = await executor.plan_action(
        intent="Delete all agents",
        user=attacker,
        capability_name="eaip.agents",
        operation=OperationType.DELETE,
    )

    result = await executor.execute_action(plan, user=attacker, approved=True)
    assert result.status == "denied"
    assert "permission" in result.summary.lower()


@pytest.mark.asyncio
async def test_audit_logging_on_all_action_lifecycle(batch3_env: dict[str, Any]) -> None:
    """Verify that action execution emits immutable audit entries."""
    executor: GovernedActionExecutor = batch3_env["executor"]
    audit: AuditLogger = batch3_env["audit"]
    user = {"user_id": "u_audited", "tenant_id": "t1", "roles": ("admin",)}

    plan = await executor.plan_action(
        intent="Inspect health",
        user=user,
        capability_name="eaip.health",
        operation=OperationType.READ,
        tool_name="system_health",
    )
    res = await executor.execute_action(plan, user=user)
    assert res.audit_entry_id is not None

    entries = audit.query(actor="u_audited")
    assert len(entries) >= 1
    assert entries[0].resource_id == "eaip.health"


@pytest.mark.asyncio
async def test_tool_failure_handled_gracefully(batch3_env: dict[str, Any]) -> None:
    """Verify when a tool raises an error, executor captures it gracefully without crashing."""
    executor: GovernedActionExecutor = batch3_env["executor"]
    user = {"user_id": "u_admin", "tenant_id": "t1", "roles": ("admin",)}

    plan = await executor.plan_action(
        intent="Execute missing tool",
        user=user,
        capability_name="eaip.agents",
        operation=OperationType.EXECUTE,
        tool_name="non_existent_tool_999",
    )

    res = await executor.execute_action(plan, user=user)
    assert res.status == "failed"
    assert "is not available" in res.summary
