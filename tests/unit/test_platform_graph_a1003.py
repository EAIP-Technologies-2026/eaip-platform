"""Unit tests for Stage A1003 — Platform Knowledge / Experience Graph."""

from __future__ import annotations

import pytest

from eaip.capabilities.inventory import load_canonical_inventory
from eaip.context.permission_context import IdentityScope
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.kgraph.platform_graph import (
    PlatformKnowledgeService,
    PlatformNodeType,
    build_platform_knowledge_graph,
)
from eaip.policy.authorization import AuthorizationManager
from eaip.policy.engine import PolicyEngine
from eaip.policy.registry import PolicyRegistry


@pytest.mark.asyncio
async def test_build_platform_knowledge_graph() -> None:
    """Verify knowledge graph build from canonical inventory."""
    registry = load_canonical_inventory()
    kg = await build_platform_knowledge_graph(registry)

    # 20 capabilities
    cap_entities = [e for e in kg._entities.values() if e.type == PlatformNodeType.CAPABILITY]
    assert len(cap_entities) == 20

    # Verify other entity types are populated
    route_entities = [e for e in kg._entities.values() if e.type == PlatformNodeType.ROUTE]
    api_entities = [e for e in kg._entities.values() if e.type == PlatformNodeType.API]
    service_entities = [e for e in kg._entities.values() if e.type == PlatformNodeType.SERVICE]
    event_entities = [e for e in kg._entities.values() if e.type == PlatformNodeType.EVENT]
    doc_entities = [e for e in kg._entities.values() if e.type == PlatformNodeType.DOCUMENTATION]
    exp_entities = [e for e in kg._entities.values() if e.type == PlatformNodeType.EXPERIENCE]

    assert len(route_entities) > 0
    assert len(api_entities) > 0
    assert len(service_entities) > 0
    assert len(event_entities) > 0
    assert len(doc_entities) > 0
    assert len(exp_entities) > 0

    # Verify edges exist
    assert len(kg._relationships) > 0


@pytest.mark.asyncio
async def test_capability_topology_query() -> None:
    """Verify querying capability topology."""
    registry = load_canonical_inventory()
    kg = await build_platform_knowledge_graph(registry)
    service = PlatformKnowledgeService(kg)

    topology = await service.get_capability_topology("eaip.agents")
    assert "error" not in topology
    assert topology["capability"].id == "cap:eaip.agents"
    assert len(topology["routes"]) == 2  # /agents, /agents/[id]
    assert len(topology["apis"]) == 3
    assert len(topology["events"]) == 4
    assert len(topology["entities"]) == 3
    assert len(topology["documentation"]) == 1
    assert len(topology["experience"]) == 1
    assert len(topology["dependencies"]) == 3  # related: orchestration, workflows, brains


@pytest.mark.asyncio
async def test_permission_scoped_knowledge_query() -> None:
    """Verify graph query filtered by PermissionAwareContext."""
    cap_registry = load_canonical_inventory()
    kg = await build_platform_knowledge_graph(cap_registry)
    service = PlatformKnowledgeService(kg)

    engine = PolicyEngine()
    policy_registry = PolicyRegistry()
    authz = AuthorizationManager(engine, policy_registry)
    resolver = PermissionContextResolver(authz, cap_registry)

    # Operator identity (cannot see eaip.administration)
    operator_identity = IdentityScope(
        user_id="user-op-2",
        tenant_id="tenant-prod",
        roles=("operator",),
    )
    operator_ctx = resolver.resolve_context(operator_identity)

    scoped_result = await service.query_scoped_knowledge(operator_ctx)
    assert scoped_result["identity"] == "user-op-2"
    assert scoped_result["tenant_id"] == "tenant-prod"
    assert scoped_result["visible_count"] == len(operator_ctx.visible_capability_ids)

    returned_caps = [c["capability_name"] for c in scoped_result["capabilities"]]
    assert "eaip.agents" in returned_caps
    assert "eaip.dashboard" in returned_caps
    assert "eaip.administration" not in returned_caps
