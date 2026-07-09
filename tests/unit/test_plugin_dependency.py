"""Tests for :mod:`eaip.plugins.dependency`."""

from __future__ import annotations

import pytest

from eaip.exceptions.domain import PluginError
from eaip.plugins.dependency import PluginDependencyValidator, _satisfies
from eaip.plugins.plugin import Plugin, PluginDependency, PluginManifest


class _TestPlugin:
    """Minimal Plugin protocol implementation for testing."""

    def __init__(self, manifest: PluginManifest) -> None:
        self.manifest = manifest

    async def activate(self, platform: object) -> None:
        pass

    async def deactivate(self, platform: object) -> None:
        pass


def _manifest(
    name: str,
    version: str = "1.0.0",
    dependencies: tuple[PluginDependency, ...] = (),
) -> PluginManifest:
    return PluginManifest(
        name=name,
        version=version,
        contract_version="1.0.0",
        dependencies=dependencies,
    )


def _plugin(
    name: str,
    version: str = "1.0.0",
    dependencies: tuple[PluginDependency, ...] = (),
) -> Plugin:
    return _TestPlugin(manifest=_manifest(name, version, dependencies))


class TestSatisfies:
    def test_any_spec(self) -> None:
        assert _satisfies("1.2.3", "*")
        assert _satisfies("1.2.3", "")

    def test_exact_match(self) -> None:
        assert _satisfies("1.2.3", "1.2.3")
        assert not _satisfies("1.2.4", "1.2.3")

    def test_greater_equal(self) -> None:
        assert _satisfies("2.0.0", ">=1.0.0")
        assert _satisfies("1.0.0", ">=1.0.0")
        assert not _satisfies("0.9.0", ">=1.0.0")

    def test_less_than(self) -> None:
        assert _satisfies("0.9.0", "<1.0.0")
        assert not _satisfies("1.0.0", "<1.0.0")

    def test_less_equal(self) -> None:
        assert _satisfies("1.0.0", "<=1.0.0")
        assert _satisfies("0.9.0", "<=1.0.0")
        assert not _satisfies("1.0.1", "<=1.0.0")

    def test_range(self) -> None:
        assert _satisfies("1.5.0", ">=1.0.0,<2.0.0")
        assert not _satisfies("2.0.0", ">=1.0.0,<2.0.0")
        assert not _satisfies("0.9.0", ">=1.0.0,<2.0.0")

    def test_pessimistic(self) -> None:
        assert _satisfies("1.2.3", "~1.2.0")
        assert _satisfies("1.2.99", "~1.2.0")
        assert not _satisfies("1.3.0", "~1.2.0")
        assert not _satisfies("1.1.0", "~1.2.0")

    def test_compatible(self) -> None:
        assert _satisfies("1.9.9", "^1.0.0")
        assert _satisfies("1.2.3", "^1.2.3")
        assert not _satisfies("2.0.0", "^1.0.0")


class TestPluginDependencyValidator:
    def test_no_dependencies(self) -> None:
        v = PluginDependencyValidator()
        plugin = _plugin("a")
        errors = v.validate(plugin, {"a": plugin})
        assert errors == []

    def test_all_satisfied(self) -> None:
        v = PluginDependencyValidator()
        base = _plugin("base", "1.0.0")
        ext = _plugin("ext", "1.0.0", dependencies=(PluginDependency(name="base"),))
        errors = v.validate(ext, {"base": base, "ext": ext})
        assert errors == []

    def test_missing_required(self) -> None:
        v = PluginDependencyValidator()
        ext = _plugin("ext", "1.0.0", dependencies=(PluginDependency(name="missing"),))
        errors = v.validate(ext, {"ext": ext})
        assert len(errors) == 1
        assert "missing" in errors[0]

    def test_missing_optional_is_warning(self) -> None:
        v = PluginDependencyValidator()
        ext = _plugin(
            "ext",
            "1.0.0",
            dependencies=(PluginDependency(name="opt", optional=True),),
        )
        errors = v.validate(ext, {"ext": ext})
        assert errors == []

    def test_version_mismatch(self) -> None:
        v = PluginDependencyValidator()
        base = _plugin("base", "0.5.0")
        ext = _plugin(
            "ext",
            "1.0.0",
            dependencies=(PluginDependency(name="base", version_spec=">=1.0.0"),),
        )
        errors = v.validate(ext, {"base": base, "ext": ext})
        assert len(errors) == 1
        assert "0.5.0" in errors[0]

    def test_optional_version_mismatch(self) -> None:
        v = PluginDependencyValidator()
        base = _plugin("base", "0.5.0")
        ext = _plugin(
            "ext",
            "1.0.0",
            dependencies=(
                PluginDependency(name="base", version_spec=">=1.0.0", optional=True),
            ),
        )
        errors = v.validate(ext, {"base": base, "ext": ext})
        assert errors == []

    def test_empty_available(self) -> None:
        v = PluginDependencyValidator()
        ext = _plugin("ext", "1.0.0", dependencies=(PluginDependency(name="base"),))
        errors = v.validate(ext, {})
        assert len(errors) == 1

    def test_topological_sort_simple(self) -> None:
        v = PluginDependencyValidator()
        base = _plugin("base", "1.0.0")
        mid = _plugin("mid", "1.0.0", dependencies=(PluginDependency(name="base"),))
        top = _plugin(
            "top",
            "1.0.0",
            dependencies=(PluginDependency(name="mid"), PluginDependency(name="base")),
        )
        sorted_ = v.topological_sort([top, mid, base])
        names = [p.manifest.name for p in sorted_]
        assert names.index("base") < names.index("mid")
        assert names.index("base") < names.index("top")
        assert names.index("mid") < names.index("top")

    def test_topological_sort_no_deps(self) -> None:
        v = PluginDependencyValidator()
        a = _plugin("a")
        b = _plugin("b")
        sorted_ = v.topological_sort([b, a])
        assert len(sorted_) == 2

    def test_circular_dependency(self) -> None:
        v = PluginDependencyValidator()
        a = _plugin("a", dependencies=(PluginDependency(name="b"),))
        b = _plugin("b", dependencies=(PluginDependency(name="a"),))
        with pytest.raises(PluginError, match="circular"):
            v.topological_sort([a, b])

    def test_self_loop(self) -> None:
        v = PluginDependencyValidator()
        a = _plugin("a", dependencies=(PluginDependency(name="a"),))
        with pytest.raises(PluginError, match="circular"):
            v.topological_sort([a])
