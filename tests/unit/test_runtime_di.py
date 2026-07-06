"""Tests for :mod:`eaip.runtime.di`."""

from __future__ import annotations

import pytest

from eaip.dependency_injection import Container, Scope
from eaip.runtime.di import RuntimeContainer


class _Engine:
    def __init__(self) -> None:
        self.started = False


class _Logger:
    def __init__(self) -> None:
        self.lines: list[str] = []


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_wraps_container() -> None:
    c = Container()
    rc = RuntimeContainer(c)
    assert rc.root is c
    assert not rc.has_active_scopes
    assert rc.active_module_scopes == []


# ---------------------------------------------------------------------------
# Resolution delegation
# ---------------------------------------------------------------------------


def test_resolve_delegates_to_root() -> None:
    c = Container()
    c.register(_Engine)
    rc = RuntimeContainer(c)

    engine = rc.resolve(_Engine)
    assert isinstance(engine, _Engine)


def test_try_resolve_returns_none_for_unknown() -> None:
    c = Container()
    rc = RuntimeContainer(c)
    assert rc.try_resolve(_Engine) is None


def test_try_resolve_returns_instance_for_registered() -> None:
    c = Container()
    c.register(_Engine)
    rc = RuntimeContainer(c)

    engine = rc.try_resolve(_Engine)
    assert isinstance(engine, _Engine)


# ---------------------------------------------------------------------------
# Module scopes
# ---------------------------------------------------------------------------


def test_create_module_scope_returns_child_container() -> None:
    c = Container()
    rc = RuntimeContainer(c)

    scope = rc.create_module_scope("my-module")
    assert scope is not c
    assert "my-module" in rc.active_module_scopes
    assert rc.has_active_scopes


def test_module_scope_shares_singletons_with_root() -> None:
    c = Container()
    c.register(_Engine, scope=Scope.SINGLETON)
    rc = RuntimeContainer(c)

    scope = rc.create_module_scope("shared-test")
    root_engine = rc.resolve(_Engine)
    scoped_engine = scope.resolve(_Engine)
    assert root_engine is scoped_engine  # same singleton


def test_module_scope_has_own_transient_instances() -> None:
    c = Container()
    c.register(_Logger, scope=Scope.TRANSIENT)
    rc = RuntimeContainer(c)

    scope = rc.create_module_scope("transient-test")
    a = scope.resolve(_Logger)
    b = scope.resolve(_Logger)
    assert a is not b


def test_get_module_scope_returns_none_for_unknown() -> None:
    c = Container()
    rc = RuntimeContainer(c)
    assert rc.get_module_scope("nonexistent") is None


def test_get_module_scope_returns_scope() -> None:
    c = Container()
    rc = RuntimeContainer(c)
    scope = rc.create_module_scope("known")
    assert rc.get_module_scope("known") is scope


# ---------------------------------------------------------------------------
# Scope lifecycle
# ---------------------------------------------------------------------------


def test_drop_module_scope_removes_scope() -> None:
    c = Container()
    rc = RuntimeContainer(c)

    rc.create_module_scope("temp")
    assert "temp" in rc.active_module_scopes

    rc.drop_module_scope("temp")
    assert "temp" not in rc.active_module_scopes
    assert not rc.has_active_scopes


def test_drop_module_scope_unknown_is_noop() -> None:
    c = Container()
    rc = RuntimeContainer(c)
    rc.drop_module_scope("nonexistent")  # should not raise


def test_multiple_module_scopes_are_independent() -> None:
    c = Container()
    rc = RuntimeContainer(c)

    scope_a = rc.create_module_scope("module-a")
    scope_b = rc.create_module_scope("module-b")

    assert scope_a is not scope_b
    assert set(rc.active_module_scopes) == {"module-a", "module-b"}

    c.register_factory(_Engine, lambda _c: _Engine(), scope=Scope.SCOPED)
    # Register in scope_a only
    scope_a.register(_Logger)

    assert scope_a.has(_Logger)
    assert not scope_b.has(_Logger)


# ---------------------------------------------------------------------------
# Integration with RuntimeHost
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_host_exposes_container() -> None:
    from eaip.application import build_platform
    from eaip.runtime.host import RuntimeHost

    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)

    assert hasattr(host, "container")
    assert isinstance(host.container, RuntimeContainer)
    # Root container should have platform subsystems registered
    assert host.container.root is platform.container
