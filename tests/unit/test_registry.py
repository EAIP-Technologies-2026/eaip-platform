"""Tests for :mod:`eaip.registry`."""

from __future__ import annotations

import pytest

from eaip.exceptions.domain import (
    DuplicateRegistrationError,
    NotFoundError,
    RegistryTypeMismatchError,
)
from eaip.registry.registry import Registry, RegistryChange, RegistryEvent


class Widget:
    def __init__(self, name: str) -> None:
        self.name = name


def test_register_and_lookup() -> None:
    r: Registry[Widget] = Registry(name="widgets", value_type=Widget)
    w = Widget("a")
    r.register("a", w)
    assert r.get("a") is w
    assert r.has("a")
    assert r.keys() == ["a"]
    assert "a" in r


def test_duplicate_rejected() -> None:
    r: Registry[Widget] = Registry(name="widgets", value_type=Widget)
    r.register("a", Widget("a"))
    with pytest.raises(DuplicateRegistrationError):
        r.register("a", Widget("a2"))


def test_replace_allowed_with_flag() -> None:
    r: Registry[Widget] = Registry(name="widgets", value_type=Widget)
    r.register("a", Widget("first"))
    r.register("a", Widget("second"), replace=True)
    assert r.get("a").name == "second"


def test_type_mismatch_rejected() -> None:
    r: Registry[Widget] = Registry(name="widgets", value_type=Widget)
    with pytest.raises(RegistryTypeMismatchError):
        r.register("a", "not a widget")  # type: ignore[arg-type]


def test_missing_raises_not_found() -> None:
    r: Registry[Widget] = Registry(name="widgets", value_type=Widget)
    with pytest.raises(NotFoundError):
        r.get("missing")


def test_unregister() -> None:
    r: Registry[Widget] = Registry(name="widgets", value_type=Widget)
    r.register("a", Widget("a"))
    assert r.unregister("a") is True
    assert r.unregister("a") is False


def test_observers_called() -> None:
    r: Registry[Widget] = Registry(name="widgets", value_type=Widget)
    events: list[RegistryChange[Widget]] = []
    remove = r.observe(events.append)
    r.register("a", Widget("a"))
    r.register("a", Widget("a2"), replace=True)
    r.unregister("a")
    remove()
    r.register("b", Widget("b"))
    assert [e.event for e in events] == [
        RegistryEvent.REGISTERED,
        RegistryEvent.REPLACED,
        RegistryEvent.UNREGISTERED,
    ]


def test_empty_key_rejected() -> None:
    r: Registry[Widget] = Registry(name="widgets", value_type=Widget)
    with pytest.raises(ValueError):
        r.register("", Widget("x"))
