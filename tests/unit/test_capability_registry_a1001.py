"""Unit tests for Stage A1001 — Capability Registry."""

from __future__ import annotations

import pytest

from eaip.capabilities.capability import (
    Capability,
    CapabilityCategory,
    CapabilityStatus,
    OperationType,
)
from eaip.capabilities.inventory import (
    CANONICAL_CAPABILITIES,
    load_canonical_inventory,
)
from eaip.capabilities.registry import CapabilityRegistry
from eaip.exceptions.domain import DuplicateRegistrationError


def test_canonical_inventory_count() -> None:
    """Verify all 20 canonical capabilities are defined."""
    assert len(CANONICAL_CAPABILITIES) == 20
    registry = load_canonical_inventory()
    assert len(registry) == 20


def test_canonical_inventory_has_required_capabilities() -> None:
    """Verify minimum required capabilities exist in registry."""
    registry = load_canonical_inventory()
    required = [
        "eaip.dashboard",
        "eaip.agents",
        "eaip.brains",
        "eaip.knowledge",
        "eaip.memory",
        "eaip.notifications",
        "eaip.operations",
        "eaip.workflows",
        "eaip.missions",
        "eaip.monitoring",
        "eaip.health",
        "eaip.administration",
        "eaip.search",
        "eaip.reports",
        "eaip.marketplace",
        "eaip.investigations",
        "eaip.orchestration",
        "eaip.guided_tour",
        "eaip.enterprise_assistant",
        "eaip.conductor",
    ]
    for cap_name in required:
        assert registry.has(cap_name), f"Missing required capability: {cap_name}"
        cap = registry.get(cap_name)
        assert cap.status is CapabilityStatus.ENABLED
        assert cap.title
        assert cap.domain == "eaip"
        assert len(cap.supported_operations) > 0


def test_duplicate_prevention() -> None:
    """Verify duplicate registration is prevented unless replace=True."""
    registry = CapabilityRegistry()
    cap = Capability(name="test.cap", title="Test Capability", version="1.0.0")
    registry.register(cap)
    with pytest.raises(DuplicateRegistrationError):
        registry.register(cap)

    # With replace=True it should succeed
    registry.register(cap, replace=True)
    assert registry.get("test.cap").name == "test.cap"


def test_category_filtering() -> None:
    """Verify filtering by capability category."""
    registry = load_canonical_inventory()
    intelligence_caps = registry.find_by_category(CapabilityCategory.INTELLIGENCE)
    names = [c.name for c in intelligence_caps]
    assert "eaip.agents" in names
    assert "eaip.brains" in names
    assert "eaip.knowledge" in names
    assert "eaip.conductor" in names

    gov_caps = registry.find_by_category(CapabilityCategory.GOVERNANCE)
    gov_names = [c.name for c in gov_caps]
    assert "eaip.administration" in gov_names
    assert "eaip.investigations" in gov_names


def test_status_filtering() -> None:
    """Verify filtering by capability lifecycle status."""
    registry = CapabilityRegistry()
    c1 = Capability(name="c1", title="C1", status=CapabilityStatus.ENABLED)
    c2 = Capability(name="c2", title="C2", status=CapabilityStatus.DISABLED)
    c3 = Capability(name="c3", title="C3", status=CapabilityStatus.DEPRECATED)
    registry.register(c1)
    registry.register(c2)
    registry.register(c3)

    assert len(registry.find_by_status(CapabilityStatus.ENABLED)) == 1
    assert len(registry.find_by_status(CapabilityStatus.DISABLED)) == 1
    assert len(registry.find_by_status(CapabilityStatus.DEPRECATED)) == 1


def test_route_filtering() -> None:
    """Verify finding capabilities by route."""
    registry = load_canonical_inventory()
    dashboard_caps = registry.find_by_route("/dashboard")
    names = [c.name for c in dashboard_caps]
    assert "eaip.dashboard" in names


def test_relationship_lookups() -> None:
    """Verify related, parent, and child relationship lookups."""
    registry = CapabilityRegistry()
    parent = Capability(
        name="eaip.parent",
        title="Parent",
        child_capabilities=("eaip.child1",),
        related_capabilities=("eaip.peer",),
    )
    child1 = Capability(
        name="eaip.child1",
        title="Child 1",
        parent_capability="eaip.parent",
    )
    child2 = Capability(
        name="eaip.child2",
        title="Child 2",
        parent_capability="eaip.parent",
    )
    peer = Capability(
        name="eaip.peer",
        title="Peer",
    )

    registry.register(parent)
    registry.register(child1)
    registry.register(child2)
    registry.register(peer)

    # Children
    children = registry.get_children("eaip.parent")
    child_names = [c.name for c in children]
    assert "eaip.child1" in child_names
    assert "eaip.child2" in child_names

    # Parent
    assert registry.get_parent("eaip.child1") == parent
    assert registry.get_parent("eaip.child2") == parent
    assert registry.get_parent("eaip.peer") is None

    # Related
    related = registry.get_related("eaip.parent")
    assert len(related) == 1
    assert related[0].name == "eaip.peer"


def test_deterministic_ordering() -> None:
    """Verify deterministic listing by name and category."""
    registry = load_canonical_inventory()
    ordered_by_name = registry.list_ordered(order_by="name")
    names = [c.name for c in ordered_by_name]
    assert names == sorted(names)

    ordered_by_cat = registry.list_ordered(order_by="category")
    assert len(ordered_by_cat) == len(registry)


def test_contract_metadata_fields() -> None:
    """Verify all fields in the extended capability contract."""
    cap = Capability(
        name="eaip.custom",
        title="Custom Capability",
        description="A test capability",
        version="1.2.3",
        capability_id="custom",
        category=CapabilityCategory.INTELLIGENCE,
        domain="eaip",
        owner="test-team",
        lifecycle_state="active",
        routes=("/custom",),
        navigation_references=("nav.custom",),
        api_operations=("GET /api/v1/custom",),
        events=("custom.event",),
        entities=("CustomEntity",),
        assistant_description="Performs custom intelligence tasks.",
        tour_metadata={"step_id": "custom", "order": "15"},
        search_terms=("custom", "test"),
        documentation_references=("docs/custom.md",),
        supported_operations=(OperationType.READ, OperationType.EXECUTE),
    )
    assert cap.id_or_name() == "custom"
    assert cap.category == CapabilityCategory.INTELLIGENCE
    assert OperationType.EXECUTE in cap.supported_operations
    assert cap.routes == ("/custom",)


def test_validation() -> None:
    """Verify capability validator."""
    registry = CapabilityRegistry()
    valid_cap = Capability(name="eaip.valid", title="Valid", version="1.0.0")
    errors = registry.validate_capability(valid_cap)
    assert len(errors) == 0
