"""Unit tests for Stage A1005 — Governed Platform Action Execution."""

from __future__ import annotations

import pytest

from eaip.admin.audit import AuditLogger
from eaip.capabilities.capability import OperationType
from eaip.capabilities.inventory import load_canonical_inventory
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.copilot.action_executor import GovernedActionExecutor
from eaip.copilot.approvals import ApprovalService
from eaip.copilot.models import RiskTier
from eaip.policy.authorization import AuthorizationManager
from eaip.policy.engine import PolicyEngine
from eaip.policy.models import Policy, PolicyEffect, PolicyRule
from eaip.policy.registry import PolicyRegistry


class MockEchoTool:
    name = "echo_tool"
    description = "Mock execution tool."

    async def execute(self, **kwargs: object) -> str:
        return '{"status": "ok", "executed": true}'


@pytest.fixture
def executor_setup() -> tuple[GovernedActionExecutor, PolicyRegistry, ApprovalService, AuditLogger]:
    cap_registry = load_canonical_inventory()
    policy_engine = PolicyEngine()
    policy_registry = PolicyRegistry()
    authz_manager = AuthorizationManager(policy_engine, policy_registry)
    resolver = PermissionContextResolver(authz_manager, cap_registry)
    approvals = ApprovalService()
    audit = AuditLogger()

    tools = {"echo_tool": MockEchoTool()}

    executor = GovernedActionExecutor(
        tools=tools,
        authz_manager=authz_manager,
        capability_registry=cap_registry,
        permission_resolver=resolver,
        approvals=approvals,
        audit=audit,
    )
    return executor, policy_registry, approvals, audit


@pytest.mark.asyncio
async def test_plan_and_execute_safe_action(
    executor_setup: tuple[GovernedActionExecutor, PolicyRegistry, ApprovalService, AuditLogger],
) -> None:
    """Verify standard authorized action plans and executes with audit trail."""
    executor, _, _, audit = executor_setup
    admin_user = {"user_id": "admin-1", "tenant_id": "tenant-1", "roles": ["admin"]}

    plan = await executor.plan_action(
        intent="Run health check",
        user=admin_user,
        capability_name="eaip.health",
        operation=OperationType.READ,
        tool_name="echo_tool",
    )
    assert plan.risk_tier is RiskTier.INFORMATIONAL
    assert plan.requires_approval is False

    result = await executor.execute_action(plan, admin_user)
    assert result.status == "executed"
    assert result.audit_entry_id is not None
    assert len(audit._store) >= 1


@pytest.mark.asyncio
async def test_approval_gated_action(
    executor_setup: tuple[GovernedActionExecutor, PolicyRegistry, ApprovalService, AuditLogger],
) -> None:
    """Verify destructive/sensitive action halts for approval before execution."""
    executor, _, approvals, _ = executor_setup
    op_user = {"user_id": "op-1", "tenant_id": "tenant-1", "roles": ["operator"]}

    plan = await executor.plan_action(
        intent="Cancel mission batch",
        user=op_user,
        capability_name="eaip.missions",
        operation=OperationType.CANCEL,
        tool_name="echo_tool",
    )
    assert plan.risk_tier is RiskTier.DESTRUCTIVE
    assert plan.requires_approval is True

    # 1. Unapproved execution attempt halts
    unapproved_result = await executor.execute_action(plan, op_user, approved=False)
    assert unapproved_result.status == "approval_required"
    assert unapproved_result.approval_id is not None
    assert unapproved_result.approval_id in approvals._requests

    # 2. Approved execution succeeds
    approved_result = await executor.execute_action(plan, op_user, approved=True)
    assert approved_result.status == "executed"


@pytest.mark.asyncio
async def test_authorization_recheck_enforcement(
    executor_setup: tuple[GovernedActionExecutor, PolicyRegistry, ApprovalService, AuditLogger],
) -> None:
    """Verify real-time policy DENY stops execution even if planned."""
    executor, policy_registry, _, _ = executor_setup

    # Register deny rule for contractor on eaip.operations
    policy = Policy(
        id="deny-contractor-ops",
        name="Deny Contractor Operations",
        rules=(
            PolicyRule(
                id="rule-deny",
                name="Deny",
                effect=PolicyEffect.DENY,
                subjects=("contractor",),
                actions=("capability:execute",),
                resources=("eaip.operations",),
                priority=100,
            ),
        ),
    )
    policy_registry.register(policy)

    contractor_user = {"user_id": "c-1", "tenant_id": "tenant-1", "roles": ["contractor"]}
    plan = await executor.plan_action(
        intent="Run maintenance",
        user=contractor_user,
        capability_name="eaip.operations",
        operation=OperationType.EXECUTE,
        tool_name="echo_tool",
    )

    result = await executor.execute_action(plan, contractor_user)
    assert result.status == "denied"
    assert "do not have permission" in result.summary


@pytest.mark.asyncio
async def test_tenant_isolation_recheck(
    executor_setup: tuple[GovernedActionExecutor, PolicyRegistry, ApprovalService, AuditLogger],
) -> None:
    """Verify cross-tenant execution attempt is blocked by real-time re-check."""
    executor, _, _, _ = executor_setup
    user_a = {"user_id": "user-a", "tenant_id": "tenant-alpha", "roles": ["operator"]}

    plan = await executor.plan_action(
        intent="Run agent in other tenant",
        user={"user_id": "user-a", "tenant_id": "tenant-beta", "roles": ["operator"]},
        capability_name="eaip.agents",
        operation=OperationType.EXECUTE,
        tool_name="echo_tool",
    )

    # Caller token is from tenant-alpha trying to execute plan targeted to tenant-beta
    result = await executor.execute_action(plan, user_a)
    assert result.status == "denied"
    assert "Cross-tenant" in result.summary
