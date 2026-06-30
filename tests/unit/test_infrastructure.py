"""Tests for :mod:`eaip.infrastructure`."""

from __future__ import annotations

import pytest

from eaip.exceptions.domain import NotFoundError
from eaip.infrastructure import EnvSecretProvider, SystemClock, UuidIdGenerator


def test_system_clock_returns_utc() -> None:
    n = SystemClock().now()
    assert n.tzinfo is not None
    assert str(n.tzinfo) == "UTC"


def test_uuid_id_generator_is_unique() -> None:
    g = UuidIdGenerator()
    ids = {g.new_id() for _ in range(100)}
    assert len(ids) == 100


def test_env_secret_get_and_require() -> None:
    p = EnvSecretProvider({"FOO": "bar"})
    assert p.get("FOO") == "bar"
    assert p.get("MISSING") is None
    assert p.require("FOO") == "bar"


def test_env_secret_require_raises_when_missing() -> None:
    p = EnvSecretProvider({})
    with pytest.raises(NotFoundError):
        p.require("MISSING")


def test_env_secret_rejects_empty_name() -> None:
    with pytest.raises(ValueError):
        EnvSecretProvider().get("")
