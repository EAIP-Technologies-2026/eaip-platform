"""Tests for enhanced Capability model with dependencies, contracts, and metadata."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.capabilities.capability import (
    Capability,
    CapabilityContract,
    CapabilityDependency,
    CapabilityStatus,
)


def _basic() -> Capability:
    return Capability(name="test.cap", title="Test", version="1.0.0")


class TestCapabilityDependency:
    def test_defaults(self) -> None:
        d = CapabilityDependency(name="base")
        assert d.name == "base"
        assert d.version_spec == "*"
        assert d.optional is False

    def test_optional(self) -> None:
        d = CapabilityDependency(name="opt", version_spec=">=1.0", optional=True)
        assert d.optional is True

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CapabilityDependency(name="")


class TestCapabilityContract:
    def test_required_fields(self) -> None:
        c = CapabilityContract(contract_version="1.0.0")
        assert c.contract_version == "1.0.0"
        assert c.event_schemas == {}

    def test_with_schemas(self) -> None:
        c = CapabilityContract(
            contract_version="1.0.0",
            event_schemas={"test.thing": "v1"},
        )
        assert c.event_schemas == {"test.thing": "v1"}


class TestCapabilityEnhanced:
    def test_defaults(self) -> None:
        c = _basic()
        assert c.depends_on == ()
        assert c.provides == ()
        assert c.contract is None
        assert c.metadata == {}

    def test_with_dependencies(self) -> None:
        deps = (CapabilityDependency(name="base"),)
        c = Capability(
            name="ext.cap",
            title="Ext",
            version="2.0.0",
            depends_on=deps,
            provides=("http.server",),
            contract=CapabilityContract(contract_version="1.0.0"),
            metadata={"maintainer": "team-a"},
            tags=("web",),
        )
        assert len(c.depends_on) == 1
        assert c.provides == ("http.server",)
        assert c.contract is not None
        assert c.metadata == {"maintainer": "team-a"}
        assert c.tags == ("web",)

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Capability(name="x", title="X", unknown="field")  # type: ignore[call-arg]

    def test_frozen(self) -> None:
        c = _basic()
        with pytest.raises(ValidationError):
            c.name = "changed"  # type: ignore[misc]

    def test_to_metadata_enabled(self) -> None:
        c = Capability(name="stable", title="Stable", version="1.0.0")
        c = c.model_copy(update={"status": CapabilityStatus.ENABLED})
        md = c.to_metadata()
        assert md.stability == "stable"

    def test_to_metadata_not_enabled(self) -> None:
        c = _basic()
        md = c.to_metadata()
        assert md.stability == "experimental"
