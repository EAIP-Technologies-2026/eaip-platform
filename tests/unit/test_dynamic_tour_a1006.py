"""Unit tests for Stage A1006 — Dynamic Guided Tour."""

from __future__ import annotations

import pytest

from eaip.admin.audit import AuditLogger
from eaip.capabilities.inventory import load_canonical_inventory
from eaip.context.permission_context import IdentityScope
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.copilot.governance import GovernancePolicy
from eaip.copilot.tour.fixtures import TourFixtureService
from eaip.copilot.tour.service import TourService
from eaip.copilot.tour.steps import (
    TOUR_STEPS,
    get_dynamic_tour_steps,
    get_tour_steps,
)
from eaip.policy.authorization import AuthorizationManager
from eaip.policy.engine import PolicyEngine
from eaip.policy.registry import PolicyRegistry


def test_static_tour_steps_preserved() -> None:
    """Verify existing 12-step baseline is preserved."""
    assert len(TOUR_STEPS) == 12
    steps = get_tour_steps()
    assert len(steps) == 12
    for step in steps:
        assert step.id
        assert step.route
        assert step.narration
        assert step.why_it_matters
        assert step.demo_safe is True


def test_permission_filtering_dynamic_steps() -> None:
    """Verify dynamic tour omits capabilities restricted from user."""
    cap_registry = load_canonical_inventory()
    policy_engine = PolicyEngine()
    policy_registry = PolicyRegistry()
    authz_manager = AuthorizationManager(policy_engine, policy_registry)
    resolver = PermissionContextResolver(authz_manager, cap_registry)

    # Operator cannot see eaip.administration
    op_identity = IdentityScope(
        user_id="op-1",
        tenant_id="tenant-1",
        roles=("operator",),
    )
    op_ctx = resolver.resolve_context(op_identity)

    op_steps = get_dynamic_tour_steps(context=op_ctx)
    step_ids = [s.id for s in op_steps]

    assert "administration" not in step_ids
    assert "agents" in step_ids
    assert "dashboard" in step_ids

    # Continuous orders
    orders = [s.order for s in op_steps]
    assert orders == list(range(len(op_steps)))


def test_contextual_start_route_alignment() -> None:
    """Verify tour can contextually start from the active route."""
    steps = get_dynamic_tour_steps(start_route="/knowledge")
    assert steps[0].route == "/knowledge"
    assert steps[0].id == "knowledge"
    assert steps[0].order == 0


@pytest.mark.asyncio
async def test_tour_service_dynamic_start() -> None:
    """Verify TourService initializes session with permission-filtered steps."""
    audit = AuditLogger()
    gov = GovernancePolicy()
    fixture_service = TourFixtureService(audit=audit)
    service = TourService(audit=audit, governance=gov, fixture_service=fixture_service)

    cap_registry = load_canonical_inventory()
    policy_engine = PolicyEngine()
    policy_registry = PolicyRegistry()
    authz = AuthorizationManager(policy_engine, policy_registry)
    resolver = PermissionContextResolver(authz, cap_registry)

    viewer_user = {"user_id": "viewer-1", "tenant_id": "tenant-1", "roles": ["viewer"]}
    viewer_ctx = resolver.resolve_context(
        IdentityScope(user_id="viewer-1", tenant_id="tenant-1", roles=("viewer",))
    )

    resp = await service.start_tour(
        viewer_user,
        permission_context=viewer_ctx,
        current_route="/dashboard",
    )

    assert resp.total_steps < 12
    assert resp.tour_session_id.startswith("tour-")
    assert resp.current_step is not None
    assert resp.current_step.id == "dashboard"
