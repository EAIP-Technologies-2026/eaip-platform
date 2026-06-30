"""Tests for :mod:`eaip.settings`."""

from __future__ import annotations

from eaip.settings import (
    CoreSettings,
    PlatformSettings,
    load_platform_settings,
)
from eaip.types import Environment


def test_defaults_load() -> None:
    s = PlatformSettings()
    assert s.core.app_name
    assert s.logging.level
    assert s.feature_flags.enabled == ()


def test_env_overrides(monkeypatch: object) -> None:
    monkeypatch.setenv("EAIP_CORE__APP_NAME", "demo")  # type: ignore[attr-defined]
    monkeypatch.setenv("EAIP_LOGGING__LEVEL", "WARNING")  # type: ignore[attr-defined]
    s = load_platform_settings()
    assert s.core.app_name == "demo"
    assert s.logging.level == "WARNING"


def test_logging_settings_to_config() -> None:
    s = PlatformSettings().logging.to_logging_config()
    assert s.level == "INFO"
    assert s.format == "json"


def test_core_environment_is_typed() -> None:
    c = CoreSettings()
    assert c.environment is Environment.LOCAL
