"""End-to-end integration test for A1001-A1003 Intelligence Foundation Batch.

Verifies the entire deterministic pipeline:
Identity -> Authorization / PolicyEngine -> A1002 Permission Context
-> A1001 Capability Registry -> A1003 Platform Knowledge Graph
-> Scoped Knowledge Delivery.
"""

from __future__ import annotations

import pytest

from eaip.capabilities.inventory import load_canonical_inventory
from eaip.context.permission_context import IdentityScope
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.kgraph.platform_graph import (
    PlatformKnowledgeService,
    build_platform_knowledge_graph,
)
from eaip.policy.authorization import AuthorizationManager
from eaip.policy.engine import PolicyEngine
from eaip.policy.registry import PolicyRegistry


@pytest.mark.asyncio
async def test_full_a1001_a1003_foundation_pipeline() -> None:
    """Validate full end-to-end pipeline across A1001, A1002, and A1003."""
    # 1. Stage A1001: Capability Registry & Canonical Inventory
    cap_registry = load_canonical_inventory()
    assert len(cap_registry) == 20
    assert cap_registry.has("eaip.agents")
    assert cap_registry.has("eaip.administration")
    assert cap_registry.has("eaip.conductor")

    # 2. Stage A1002: Permission-Aware Context Resolution
    policy_engine = PolicyEngine()
    policy_registry = PolicyRegistry()
    authz_manager = AuthorizationManager(policy_engine, policy_registry)
    resolver = PermissionContextResolver(authz_manager, cap_registry)

    admin_user = IdentityScope(
        user_id="sec-admin-001",
        tenant_id="tenant-core",
        roles=("admin",),
    )
    operator_user = IdentityScope(
        user_id="sre-operator-002",
        tenant_id="tenant-core",
        roles=("operator",),
    )
    auditor_user = IdentityScope(
        user_id="compliance-003",
        tenant_id="tenant-core",
        roles=("auditor",),
    )

    admin_ctx = resolver.resolve_context(admin_user)
    operator_ctx = resolver.resolve_context(operator_user)
    auditor_ctx = resolver.resolve_context(auditor_user)

    # Admin: Full capability access
    assert len(admin_ctx.visible_capability_ids) == 20
    assert len(admin_ctx.executable_capability_ids) == 20
    assert admin_ctx.can_see("eaip.administration") is True
    assert admin_ctx.can_act("eaip.administration") is True

    # Operator: Operational/intelligence execution, governance restricted
    assert operator_ctx.can_see("eaip.agents") is True
    assert operator_ctx.can_act("eaip.agents") is True
    assert operator_ctx.can_see("eaip.administration") is False
    assert operator_ctx.can_act("eaip.administration") is False
    assert operator_ctx.requires_approval("eaip.operations") is True

    # Auditor: Read-only visibility, zero execution
    assert auditor_ctx.can_see("eaip.administration") is True
    assert auditor_ctx.can_act("eaip.administration") is False
    assert len(auditor_ctx.executable_capability_ids) == 0

    # 3. Stage A1003: Platform Knowledge / Experience Graph Build & Topology
    kg = await build_platform_knowledge_graph(cap_registry)
    kg_service = PlatformKnowledgeService(kg)

    # Topology query for eaip.conductor
    conductor_topo = await kg_service.get_capability_topology("eaip.conductor")
    assert conductor_topo["capability"].id == "cap:eaip.conductor"
    assert len(conductor_topo["apis"]) >= 2
    assert len(conductor_topo["events"]) >= 3
    assert len(conductor_topo["dependencies"]) >= 2

    # 4. Scoped Knowledge Query per Identity Context
    admin_scoped = await kg_service.query_scoped_knowledge(admin_ctx)
    operator_scoped = await kg_service.query_scoped_knowledge(operator_ctx)

    admin_cap_names = [c["capability_name"] for c in admin_scoped["capabilities"]]
    operator_cap_names = [c["capability_name"] for c in operator_scoped["capabilities"]]

    assert "eaip.administration" in admin_cap_names
    assert "eaip.administration" not in operator_cap_names
    assert "eaip.agents" in operator_cap_names
    assert operator_scoped["visible_count"] == len(operator_ctx.visible_capability_ids)
