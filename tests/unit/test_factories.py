"""Tests for :mod:`eaip.factories`."""

from __future__ import annotations

import pytest

from eaip.exceptions.domain import DuplicateRegistrationError, NotFoundError
from eaip.factories import Factory


def test_register_and_create() -> None:
    f: Factory[str] = Factory(name="greeters")
    f.register("hello", lambda name: f"hello {name}")
    assert f.create("hello", name="ada") == "hello ada"


def test_duplicate_raises_unless_replace() -> None:
    f: Factory[str] = Factory(name="x")
    f.register("k", lambda: "v1")
    with pytest.raises(DuplicateRegistrationError):
        f.register("k", lambda: "v2")
    f.register("k", lambda: "v2", replace=True)
    assert f.create("k") == "v2"


def test_missing_raises_not_found() -> None:
    f: Factory[int] = Factory(name="x")
    with pytest.raises(NotFoundError):
        f.create("missing")


def test_unregister_and_contains() -> None:
    f: Factory[int] = Factory(name="x")
    f.register("k", lambda: 1)
    assert "k" in f and len(f) == 1
    assert f.unregister("k") is True
    assert "k" not in f and f.unregister("k") is False
