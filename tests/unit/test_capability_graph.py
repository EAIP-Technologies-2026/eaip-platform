"""Tests for :mod:`eaip.capabilities.graph`."""

from __future__ import annotations

import pytest

from eaip.capabilities.capability import Capability, CapabilityDependency
from eaip.capabilities.graph import CapabilityGraph
from eaip.exceptions.domain import DependencyCycleError


def _cap(name: str, deps: tuple[CapabilityDependency, ...] = ()) -> Capability:
    return Capability(name=name, title=name, version="1.0.0", depends_on=deps)


class TestCapabilityGraph:
    def test_empty_graph(self) -> None:
        g = CapabilityGraph([])
        assert g.count == 0
        assert list(g.topological_sort()) == []

    def test_single_node(self) -> None:
        g = CapabilityGraph([_cap("a")])
        assert g.count == 1
        assert [c.name for c in g.topological_sort()] == ["a"]

    def test_dag(self) -> None:
        base = _cap("base")
        mid = _cap("mid", deps=(CapabilityDependency(name="base"),))
        top = _cap("top", deps=(CapabilityDependency(name="mid"),))
        g = CapabilityGraph([top, mid, base])
        names = [c.name for c in g.topological_sort()]
        assert names.index("base") < names.index("mid")
        assert names.index("mid") < names.index("top")

    def test_cycle_detected(self) -> None:
        a = _cap("a", deps=(CapabilityDependency(name="b"),))
        b = _cap("b", deps=(CapabilityDependency(name="a"),))
        with pytest.raises(DependencyCycleError):
            CapabilityGraph([a, b])

    def test_self_loop(self) -> None:
        a = _cap("a", deps=(CapabilityDependency(name="a"),))
        with pytest.raises(DependencyCycleError):
            CapabilityGraph([a])

    def test_diamond(self) -> None:
        root = _cap("root")
        left = _cap("left", deps=(CapabilityDependency(name="root"),))
        right = _cap("right", deps=(CapabilityDependency(name="root"),))
        leaf = _cap(
            "leaf",
            deps=(CapabilityDependency(name="left"), CapabilityDependency(name="right")),
        )
        g = CapabilityGraph([leaf, right, left, root])
        names = [c.name for c in g.topological_sort()]
        assert names.index("root") == 0
        assert names.index("leaf") == len(names) - 1

    def test_has_get(self) -> None:
        g = CapabilityGraph([_cap("a")])
        assert g.has("a")
        assert not g.has("b")
        assert g.get("a").name == "a"

    def test_get_missing_raises(self) -> None:
        g = CapabilityGraph([])
        with pytest.raises(Exception):
            g.get("missing")

    def test_dependencies(self) -> None:
        a = _cap("a", deps=(CapabilityDependency(name="b"), CapabilityDependency(name="c")))
        g = CapabilityGraph([a, _cap("b"), _cap("c")])
        assert set(g.dependencies("a")) == {"b", "c"}
        assert g.dependencies("b") == []

    def test_optional_not_in_deps(self) -> None:
        a = _cap("a", deps=(CapabilityDependency(name="b", optional=True),))
        g = CapabilityGraph([a, _cap("b")])
        assert g.dependencies("a") == []

    def test_dependents(self) -> None:
        root = _cap("root")
        dep = _cap("dep", deps=(CapabilityDependency(name="root"),))
        g = CapabilityGraph([dep, root])
        assert g.dependents("root") == ["dep"]
        assert g.dependents("dep") == []

    def test_transitive_dependencies(self) -> None:
        a = _cap("a")
        b = _cap("b", deps=(CapabilityDependency(name="a"),))
        c = _cap("c", deps=(CapabilityDependency(name="b"),))
        g = CapabilityGraph([c, b, a])
        assert g.transitive_dependencies("c") == ["b", "a"]
        assert g.transitive_dependencies("a") == []

    def test_transitive_dependents(self) -> None:
        a = _cap("a")
        b = _cap("b", deps=(CapabilityDependency(name="a"),))
        c = _cap("c", deps=(CapabilityDependency(name="b"),))
        g = CapabilityGraph([c, b, a])
        assert g.transitive_dependents("a") == ["b", "c"]
        assert g.transitive_dependents("c") == []

    def test_contains(self) -> None:
        g = CapabilityGraph([_cap("a")])
        assert "a" in g
        assert "b" not in g

    def test_len(self) -> None:
        g = CapabilityGraph([_cap("a"), _cap("b")])
        assert len(g) == 2
