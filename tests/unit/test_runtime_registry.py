"""Unit tests for :mod:`eaip.runtime.registry`."""

from __future__ import annotations

from eaip.runtime.module import BaseRuntimeModule
from eaip.runtime.registry import RuntimeRegistry


class _Mod(BaseRuntimeModule):
    module_name = "test-mod"
    module_dependencies = ("a", "b")

    async def on_start(self, host: object, ctx: object) -> None:
        pass


def test_register_and_get_entry() -> None:
    reg = RuntimeRegistry()
    mod = _Mod()
    reg.register_module(mod)

    entry = reg.get_entry("test-mod")
    assert entry is not None
    assert entry.name == "test-mod"
    assert entry.dependencies == ("a", "b")
    assert entry.registered_at is not None


def test_get_entry_returns_none_for_unknown() -> None:
    reg = RuntimeRegistry()
    assert reg.get_entry("nope") is None


def test_unregister_removes_entry() -> None:
    reg = RuntimeRegistry()
    mod = _Mod()
    reg.register_module(mod)
    assert reg.has_module("test-mod")
    assert reg.unregister_module("test-mod") is True
    assert not reg.has_module("test-mod")


def test_unregister_unknown_returns_false() -> None:
    reg = RuntimeRegistry()
    assert reg.unregister_module("nope") is False


def test_module_names_sorted() -> None:
    reg = RuntimeRegistry()
    reg.register_module(_Mod())
    assert reg.module_names() == ["test-mod"]


def test_module_count() -> None:
    reg = RuntimeRegistry()
    assert reg.module_count() == 0
    reg.register_module(_Mod())
    assert reg.module_count() == 1


def test_has_module() -> None:
    reg = RuntimeRegistry()
    assert not reg.has_module("test-mod")
    reg.register_module(_Mod())
    assert reg.has_module("test-mod")


def test_health_status() -> None:
    reg = RuntimeRegistry()
    reg.register_module(_Mod())
    assert reg.get_health_status("test-mod") is None
    reg.set_health_status("test-mod", "healthy")
    assert reg.get_health_status("test-mod") == "healthy"


def test_module_metadata() -> None:
    reg = RuntimeRegistry()
    reg.register_module(_Mod())
    meta = reg.module_metadata("test-mod")
    assert meta is not None
    assert meta["name"] == "test-mod"
    assert meta["dependencies"] == ["a", "b"]
    assert "registered_at" in meta
    assert meta["health_status"] is None

    reg.set_health_status("test-mod", "healthy")
    meta = reg.module_metadata("test-mod")
    assert meta["health_status"] == "healthy"


def test_module_metadata_unknown() -> None:
    reg = RuntimeRegistry()
    assert reg.module_metadata("nope") is None


def test_all_metadata() -> None:
    reg = RuntimeRegistry()
    reg.register_module(_Mod())
    all_meta = reg.all_metadata()
    assert "test-mod" in all_meta
    assert all_meta["test-mod"]["name"] == "test-mod"


def test_clear() -> None:
    reg = RuntimeRegistry()
    reg.register_module(_Mod())
    reg.set_health_status("test-mod", "healthy")
    reg.clear()
    assert reg.module_count() == 0
    assert reg.get_health_status("test-mod") is None
