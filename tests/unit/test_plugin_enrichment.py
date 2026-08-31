"""Tests for enhanced PluginManifest with PluginDependency."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.plugins.plugin import PluginDependency, PluginManifest


def test_plugin_dependency_defaults() -> None:
    dep = PluginDependency(name="foo")
    assert dep.name == "foo"
    assert dep.version_spec == "*"
    assert dep.optional is False


def test_plugin_dependency_optional() -> None:
    dep = PluginDependency(name="bar", version_spec=">=1.0.0", optional=True)
    assert dep.optional is True
    assert dep.version_spec == ">=1.0.0"


def test_plugin_dependency_empty_name_rejected() -> None:
    with pytest.raises(ValidationError):
        PluginDependency(name="")


def test_manifest_defaults() -> None:
    m = PluginManifest(name="test", version="1.0.0")
    assert m.contract_version == "1.0.0"
    assert m.entry_point == ""
    assert m.requires_platform == ">=0.1.0"
    assert m.tags == ()
    assert m.dependencies == ()


def test_manifest_with_dependencies() -> None:
    deps = (
        PluginDependency(name="base", version_spec=">=0.1.0"),
        PluginDependency(name="opt", version_spec="~1.0.0", optional=True),
    )
    m = PluginManifest(
        name="ext",
        version="2.0.0",
        description="Extended plugin",
        contract_version="1.0.0",
        entry_point="myext.plugin:MyPlugin",
        requires_platform=">=0.2.0",
        tags=("analytics", "metrics"),
        dependencies=deps,
    )
    assert m.name == "ext"
    assert m.version == "2.0.0"
    assert m.entry_point == "myext.plugin:MyPlugin"
    assert m.requires_platform == ">=0.2.0"
    assert m.tags == ("analytics", "metrics")
    assert len(m.dependencies) == 2


def test_manifest_frozen() -> None:
    m = PluginManifest(name="test", version="1.0.0")
    with pytest.raises(ValidationError):
        m.name = "changed"  # type: ignore[misc]


def test_manifest_extra_forbidden() -> None:
    with pytest.raises(ValidationError):
        PluginManifest(name="test", version="1.0.0", unknown="extra")


def test_to_metadata() -> None:
    m = PluginManifest(
        name="pkg",
        version="0.1.0",
        description="Test plugin",
        tags=("foo",),
    )
    md = m.to_metadata()
    assert md.name == "pkg"
    assert md.version == "0.1.0"
    assert md.description == "Test plugin"
    assert md.tags == ("foo",)


def test_to_metadata_falls_back_to_provides_capabilities() -> None:
    m = PluginManifest(name="legacy", version="1.0.0", provides_capabilities=("cap1",))
    md = m.to_metadata()
    assert md.tags == ("cap1",)
