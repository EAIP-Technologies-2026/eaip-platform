"""Tests for :mod:`eaip.dependency_injection`."""

from __future__ import annotations

import pytest

from eaip.dependency_injection import Container, Scope
from eaip.exceptions.domain import (
    DependencyCycleError,
    DuplicateRegistrationError,
    NotFoundError,
    RegistryTypeMismatchError,
)


class Iface: ...


class Impl(Iface):
    def __init__(self) -> None:
        self.value = "ok"


class OtherImpl(Iface): ...


def test_register_instance_and_resolve() -> None:
    c = Container()
    impl = Impl()
    c.register_instance(Iface, impl)
    assert c.resolve(Iface) is impl


def test_register_type() -> None:
    c = Container()
    c.register(Iface, Impl)
    assert isinstance(c.resolve(Iface), Impl)


def test_register_factory_singleton() -> None:
    c = Container()
    c.register_factory(Iface, lambda _c: Impl(), scope=Scope.SINGLETON)
    a = c.resolve(Iface)
    b = c.resolve(Iface)
    assert a is b  # singleton


def test_register_factory_transient() -> None:
    c = Container()
    c.register_factory(Iface, lambda _c: Impl(), scope=Scope.TRANSIENT)
    assert c.resolve(Iface) is not c.resolve(Iface)


def test_duplicate_registration_raises() -> None:
    c = Container()
    c.register(Iface, Impl)
    with pytest.raises(DuplicateRegistrationError):
        c.register(Iface, OtherImpl)


def test_factory_type_mismatch_detected() -> None:
    c = Container()
    c.register_factory(Iface, lambda _c: "not an Iface")  # type: ignore[arg-type,return-value]
    with pytest.raises(RegistryTypeMismatchError):
        c.resolve(Iface)


def test_unknown_key_raises_not_found() -> None:
    c = Container()
    with pytest.raises(NotFoundError):
        c.resolve(Iface)
    assert c.try_resolve(Iface) is None


def test_cycle_detection() -> None:
    class A: ...

    class B: ...

    c = Container()
    c.register_factory(A, lambda cc: cc.resolve(B))  # type: ignore[arg-type,return-value]
    c.register_factory(B, lambda cc: cc.resolve(A))  # type: ignore[arg-type,return-value]
    with pytest.raises(DependencyCycleError):
        c.resolve(A)


def test_scope_parent_share_singletons() -> None:
    c = Container()
    c.register(Iface, Impl)
    child = c.create_scope()
    assert c.resolve(Iface) is child.resolve(Iface)


def test_register_instance_validates_type() -> None:
    c = Container()
    with pytest.raises(RegistryTypeMismatchError):
        c.register_instance(Iface, "not an Iface")  # type: ignore[arg-type]
