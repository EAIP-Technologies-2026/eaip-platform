"""Tests for :mod:`eaip.capabilities.resolution`."""

from __future__ import annotations

import pytest

from eaip.capabilities.capability import Capability
from eaip.capabilities.graph import CapabilityGraph
from eaip.capabilities.resolution import CapabilityResolver


def _cap(name: str, version: str = "1.0.0") -> Capability:
    return Capability(name=name, title=name, version=version)


class TestCapabilityResolver:
    def test_resolve_exact(self) -> None:
        g = CapabilityGraph([_cap("a", "1.0.0")])
        r = CapabilityResolver()
        cap = r.resolve(g, "a", "1.0.0")
        assert cap is not None
        assert cap.name == "a"

    def test_resolve_wildcard(self) -> None:
        g = CapabilityGraph([_cap("a", "1.0.0")])
        r = CapabilityResolver()
        cap = r.resolve(g, "a", "*")
        assert cap is not None

    def test_resolve_missing(self) -> None:
        g = CapabilityGraph([])
        r = CapabilityResolver()
        assert r.resolve(g, "missing") is None

    def test_resolve_version_mismatch(self) -> None:
        g = CapabilityGraph([_cap("a", "1.0.0")])
        r = CapabilityResolver()
        assert r.resolve(g, "a", ">=2.0.0") is None

    def test_resolve_all_success(self) -> None:
        g = CapabilityGraph([_cap("a", "1.0.0"), _cap("b", "2.0.0")])
        r = CapabilityResolver()
        result = r.resolve_all(g, {"a": "*", "b": ">=1.0.0"})
        assert len(result) == 2

    def test_resolve_all_missing_raises(self) -> None:
        g = CapabilityGraph([_cap("a", "1.0.0")])
        r = CapabilityResolver()
        with pytest.raises(ValueError, match="unresolved"):
            r.resolve_all(g, {"a": "*", "missing": "*"})
