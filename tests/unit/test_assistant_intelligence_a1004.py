"""Unit tests for Stage A1004 — Assistant Intelligence."""

from __future__ import annotations

import pytest

from eaip.capabilities.inventory import load_canonical_inventory
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.copilot.intelligence import (
    AssistantIntelligenceService,
)
from eaip.kgraph.platform_graph import (
    PlatformKnowledgeService,
    build_platform_knowledge_graph,
)
from eaip.policy.authorization import AuthorizationManager
from eaip.policy.engine import PolicyEngine
from eaip.policy.registry import PolicyRegistry


@pytest.fixture
async def intelligence_service() -> AssistantIntelligenceService:
    cap_registry = load_canonical_inventory()
    policy_engine = PolicyEngine()
    policy_registry = PolicyRegistry()
    authz_manager = AuthorizationManager(policy_engine, policy_registry)
    resolver = PermissionContextResolver(authz_manager, cap_registry)
    kg = await build_platform_knowledge_graph(cap_registry)
    kg_service = PlatformKnowledgeService(kg)
    return AssistantIntelligenceService(cap_registry, resolver, kg_service)


@pytest.mark.asyncio
async def test_current_page_intelligence(
    intelligence_service: AssistantIntelligenceService,
) -> None:
    """Verify assistant explains the active route context."""
    user = {"user_id": "op-1", "tenant_id": "tenant-1", "roles": ["operator"]}
    resp = await intelligence_service.answer_grounded_query(
        message="What is this page?",
        user=user,
        current_route="/agents",
    )
    assert resp.grounded_capability == "eaip.agents"
    assert "Autonomous Agents" in resp.reply
    assert "/agents" in resp.sources
    assert resp.confidence == 1.0
    assert resp.is_uncertain is False


@pytest.mark.asyncio
async def test_capability_query_grounding(
    intelligence_service: AssistantIntelligenceService,
) -> None:
    """Verify grounded capability lookup with citations and suggestions."""
    user = {"user_id": "admin-1", "tenant_id": "tenant-1", "roles": ["admin"]}
    resp = await intelligence_service.answer_grounded_query(
        message="Tell me about Conductor Copilot",
        user=user,
        current_route="/dashboard",
    )
    assert resp.grounded_capability == "eaip.conductor"
    assert "Conductor Copilot Engine" in resp.reply
    assert len(resp.sources) > 0
    assert len(resp.suggested_actions) > 0


@pytest.mark.asyncio
async def test_capabilities_discovery(
    intelligence_service: AssistantIntelligenceService,
) -> None:
    """Verify user can discover authorized capabilities."""
    user = {"user_id": "viewer-1", "tenant_id": "tenant-1", "roles": ["viewer"]}
    resp = await intelligence_service.answer_grounded_query(
        message="What capabilities can I access?",
        user=user,
        current_route="/dashboard",
    )
    assert "Available Capabilities" in resp.reply
    assert "Autonomous Agents" in resp.reply
    assert "Read-only" in resp.reply


@pytest.mark.asyncio
async def test_restricted_role_visibility(
    intelligence_service: AssistantIntelligenceService,
) -> None:
    """Verify restricted capabilities are not leaked to unauthorized roles."""
    operator_user = {"user_id": "op-1", "tenant_id": "tenant-1", "roles": ["operator"]}
    resp = await intelligence_service.answer_grounded_query(
        message="Tell me about Platform Administration",
        user=operator_user,
        current_route="/dashboard",
    )
    assert "restricted from viewing its details" in resp.reply
    assert resp.grounded_capability == "eaip.administration"


@pytest.mark.asyncio
async def test_anti_hallucination_unknown_concept(
    intelligence_service: AssistantIntelligenceService,
) -> None:
    """Verify assistant refuses to fabricate unknown concepts."""
    user = {"user_id": "user-1", "tenant_id": "tenant-1", "roles": ["admin"]}
    resp = await intelligence_service.answer_grounded_query(
        message="Explain the Quantum Fusion Supercomputer inside EAIP",
        user=user,
        current_route="/dashboard",
    )
    assert resp.is_uncertain is True
    assert resp.confidence == 0.0
    assert "don't have sufficient platform evidence" in resp.reply
    assert resp.grounded_capability is None
