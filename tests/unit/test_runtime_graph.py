"""Unit tests for :mod:`eaip.runtime.graph`."""

from __future__ import annotations

import pytest

from eaip.runtime.exceptions import DependencyResolutionError
from eaip.runtime.graph import DependencyGraph
from eaip.runtime.module import BaseRuntimeModule


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class _Mod(BaseRuntimeModule):
    """Minimal concrete module for testing."""

    def __init__(self, name: str, deps: tuple[str, ...] = ()) -> None:
        self.module_name = name
        self.module_dependencies = deps

    async def on_start(self, host: object, ctx: object) -> None:  # type: ignore[override]
        pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_single_module_no_deps() -> None:
    a = _Mod("a")
    g = DependencyGraph([a])
    assert g.ordered() == [a]


def test_linear_order_respected() -> None:
    a = _Mod("a")
    b = _Mod("b", deps=("a",))
    c = _Mod("c", deps=("b",))
    g = DependencyGraph([c, b, a])  # passed out of order
    ordered = g.ordered()
    names = [m.name for m in ordered]
    assert names.index("a") < names.index("b") < names.index("c")


def test_diamond_dependency() -> None:
    #  a → b → d
    #  a → c → d
    a = _Mod("a")
    b = _Mod("b", deps=("a",))
    c = _Mod("c", deps=("a",))
    d = _Mod("d", deps=("b", "c"))
    g = DependencyGraph([a, b, c, d])
    ordered = g.ordered()
    names = [m.name for m in ordered]
    assert names.index("a") < names.index("b")
    assert names.index("a") < names.index("c")
    assert names.index("b") < names.index("d")
    assert names.index("c") < names.index("d")


def test_independent_modules_sorted_alphabetically() -> None:
    z = _Mod("z")
    a = _Mod("a")
    m = _Mod("m")
    g = DependencyGraph([z, m, a])
    names = [mod.name for mod in g.ordered()]
    assert names == ["a", "m", "z"]


def test_duplicate_name_raises() -> None:
    a1 = _Mod("a")
    a2 = _Mod("a")
    with pytest.raises(DependencyResolutionError, match="duplicate"):
        DependencyGraph([a1, a2])


def test_unknown_dependency_raises() -> None:
    a = _Mod("a", deps=("nonexistent",))
    g = DependencyGraph([a])
    with pytest.raises(DependencyResolutionError, match="unknown dependency"):
        g.ordered()


def test_cycle_raises() -> None:
    a = _Mod("a", deps=("b",))
    b = _Mod("b", deps=("a",))
    g = DependencyGraph([a, b])
    with pytest.raises(DependencyResolutionError, match="circular"):
        g.ordered()


def test_empty_graph() -> None:
    g = DependencyGraph([])
    assert g.ordered() == []
    assert len(g) == 0


def test_len_and_contains() -> None:
    a = _Mod("a")
    b = _Mod("b")
    g = DependencyGraph([a, b])
    assert len(g) == 2
    assert "a" in g
    assert "z" not in g


def test_names_are_sorted() -> None:
    z = _Mod("z")
    a = _Mod("a")
    g = DependencyGraph([z, a])
    assert g.names() == ["a", "z"]
