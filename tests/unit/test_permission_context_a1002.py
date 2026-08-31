"""Unit tests for Stage A1002 — Permission-Aware Context."""

from __future__ import annotations

import pytest

from eaip.capabilities.inventory import load_canonical_inventory
from eaip.context.permission_context import (
    IdentityScope,
)
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.policy.authorization import AuthorizationManager
from eaip.policy.engine import PolicyEngine
from eaip.policy.models import (
    Policy,
    PolicyEffect,
    PolicyRule,
)
from eaip.policy.registry import PolicyRegistry


@pytest.fixture
def authz_and_registry() -> tuple[AuthorizationManager, PolicyRegistry]:
    engine = PolicyEngine()
    registry = PolicyRegistry()
    authz = AuthorizationManager(engine, registry)
    return authz, registry


def test_admin_context_resolution(
    authz_and_registry: tuple[AuthorizationManager, PolicyRegistry],
) -> None:
    """Verify administrator identity resolves full visibility and execution."""
    authz, _ = authz_and_registry
    cap_registry = load_canonical_inventory()
    resolver = PermissionContextResolver(authz, cap_registry)

    admin_identity = IdentityScope(
        user_id="user-admin-1",
        tenant_id="tenant-1",
        roles=("admin",),
    )

    ctx = resolver.resolve_context(admin_identity)
    assert ctx.identity.user_id == "user-admin-1"
    assert len(ctx.visible_capability_ids) == 20
    assert len(ctx.executable_capability_ids) == 20
    assert len(ctx.restricted_capability_ids) == 0

    assert ctx.can_see("eaip.administration") is True
    assert ctx.can_act("eaip.administration") is True
    assert ctx.can_act("eaip.agents") is True
    assert ctx.requires_approval("eaip.operations") is False


def test_operator_context_resolution(
    authz_and_registry: tuple[AuthorizationManager, PolicyRegistry],
) -> None:
    """Verify operator identity resolves execution with approval requirements on sensitive ops."""
    authz, _ = authz_and_registry
    cap_registry = load_canonical_inventory()
    resolver = PermissionContextResolver(authz, cap_registry)

    operator_identity = IdentityScope(
        user_id="user-op-1",
        tenant_id="tenant-1",
        roles=("operator",),
    )

    ctx = resolver.resolve_context(operator_identity)
    assert ctx.can_see("eaip.agents") is True
    assert ctx.can_act("eaip.agents") is True

    # Sensitive operations require approval
    assert ctx.requires_approval("eaip.operations") is True
    assert ctx.requires_approval("eaip.missions") is True

    # Governance / Administration is restricted
    assert ctx.can_see("eaip.administration") is False
    assert ctx.can_act("eaip.administration") is False
    assert ctx.is_restricted("eaip.administration") is True


def test_auditor_context_resolution(
    authz_and_registry: tuple[AuthorizationManager, PolicyRegistry],
) -> None:
    """Verify auditor identity can see/read all capabilities but cannot execute or mutate."""
    authz, _ = authz_and_registry
    cap_registry = load_canonical_inventory()
    resolver = PermissionContextResolver(authz, cap_registry)

    auditor_identity = IdentityScope(
        user_id="user-audit-1",
        tenant_id="tenant-1",
        roles=("auditor",),
    )

    ctx = resolver.resolve_context(auditor_identity)
    assert ctx.can_see("eaip.administration") is True
    assert ctx.can_see("eaip.investigations") is True
    assert ctx.can_see("eaip.agents") is True

    # Auditor cannot execute actions
    assert ctx.can_act("eaip.agents") is False
    assert ctx.can_act("eaip.administration") is False
    assert len(ctx.executable_capability_ids) == 0


def test_tenant_isolation_enforcement(
    authz_and_registry: tuple[AuthorizationManager, PolicyRegistry],
) -> None:
    """Verify cross-tenant requests are strictly blocked unless system administrator."""
    authz, _ = authz_and_registry
    cap_registry = load_canonical_inventory()
    resolver = PermissionContextResolver(authz, cap_registry)

    tenant_a_user = IdentityScope(
        user_id="user-a-1",
        tenant_id="tenant-alpha",
        roles=("operator",),
    )

    # Attempting to access tenant-beta without cross-tenant admin
    cross_tenant_ctx = resolver.resolve_context(tenant_a_user, target_tenant_id="tenant-beta")
    assert len(cross_tenant_ctx.visible_capability_ids) == 0
    assert len(cross_tenant_ctx.executable_capability_ids) == 0
    assert len(cross_tenant_ctx.restricted_capability_ids) == 20

    # Same user accessing their own tenant-alpha succeeds
    own_tenant_ctx = resolver.resolve_context(tenant_a_user, target_tenant_id="tenant-alpha")
    assert len(own_tenant_ctx.visible_capability_ids) > 0


def test_custom_policy_denial_without_bypass(
    authz_and_registry: tuple[AuthorizationManager, PolicyRegistry],
) -> None:
    """Verify explicit DENY policy in PolicyRegistry is respected without bypass."""
    authz, policy_registry = authz_and_registry
    cap_registry = load_canonical_inventory()
    resolver = PermissionContextResolver(authz, cap_registry)

    # Register policy denying access to agents for restricted users
    policy = Policy(
        id="policy-deny-agents",
        name="Deny Agents for Contractors",
        rules=(
            PolicyRule(
                id="rule-deny-agents",
                name="Deny agents",
                effect=PolicyEffect.DENY,
                subjects=("contractor",),
                actions=("capability:read", "capability:invoke"),
                resources=("eaip.agents",),
                priority=100,
            ),
        ),
    )
    policy_registry.register(policy)

    contractor_identity = IdentityScope(
        user_id="user-contractor-1",
        tenant_id="tenant-1",
        roles=("contractor",),
    )

    ctx = resolver.resolve_context(contractor_identity)
    assert ctx.can_see("eaip.agents") is False
    assert ctx.can_act("eaip.agents") is False
    assert ctx.is_restricted("eaip.agents") is True
