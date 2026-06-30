"""Tests for :mod:`eaip.types`."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from eaip.types import EnvName, Environment, HostName, LogLevel, NonEmptyStr, Port, Url


class _Cfg(BaseModel):
    name: NonEmptyStr
    port: Port
    host: HostName
    url: Url
    level: LogLevel
    env: EnvName


def test_happy_path() -> None:
    cfg = _Cfg(
        name="  app  ",
        port=8080,
        host="example.com",
        url="https://example.com/path",
        level="debug",
        env="prod-eu",
    )
    assert cfg.name == "app"
    assert cfg.level == "DEBUG"


@pytest.mark.parametrize("port", [0, -1, 65_536, 1_000_000])
def test_port_out_of_range(port: int) -> None:
    with pytest.raises(ValidationError):
        _Cfg(name="x", port=port, host="x", url="http://x", level="INFO", env="x")


def test_empty_name_rejected() -> None:
    with pytest.raises(ValidationError):
        _Cfg(name="   ", port=1, host="x", url="http://x", level="INFO", env="x")


def test_url_requires_scheme() -> None:
    with pytest.raises(ValidationError):
        _Cfg(name="x", port=1, host="x", url="no-scheme", level="INFO", env="x")


def test_log_level_canonicalised() -> None:
    cfg = _Cfg(name="x", port=1, host="x", url="http://x", level="warning", env="x")
    assert cfg.level == "WARNING"


def test_invalid_log_level() -> None:
    with pytest.raises(ValidationError):
        _Cfg(name="x", port=1, host="x", url="http://x", level="verbose", env="x")


class TestEnvironment:
    def test_parses_aliases(self) -> None:
        assert Environment.parse("dev") is Environment.DEVELOPMENT
        assert Environment.parse("PROD") is Environment.PRODUCTION
        assert Environment.parse("staging") is Environment.STAGING

    def test_production_like(self) -> None:
        assert Environment.PRODUCTION.is_production_like
        assert Environment.STAGING.is_production_like
        assert not Environment.LOCAL.is_production_like

    def test_rejects_garbage(self) -> None:
        with pytest.raises(ValueError):
            Environment.parse("mars")
