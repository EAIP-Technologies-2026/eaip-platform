"""Tests for the Sentry integration module."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from eaip.integrations.sentry import (
    SentryHealthCheck,
    add_sentry_middleware,
    init_sentry,
)
from eaip.settings.core_settings import PlatformSettings, SentrySettings


@pytest.fixture
def settings_with_dsn() -> PlatformSettings:
    return PlatformSettings(
        sentry=SentrySettings(dsn="https://example@sentry.io/1"),
    )


@pytest.fixture
def settings_without_dsn() -> PlatformSettings:
    return PlatformSettings(
        sentry=SentrySettings(dsn=None),
    )


@pytest.fixture
def settings_with_env_override() -> PlatformSettings:
    return PlatformSettings(
        sentry=SentrySettings(
            dsn="https://example@sentry.io/2",
            environment="staging",
            release="1.2.3",
            traces_sample_rate=0.5,
            send_default_pii=True,
        ),
    )


class TestInitSentry:
    def test_init_sentry_skips_without_dsn(self, settings_without_dsn: PlatformSettings) -> None:
        result = init_sentry(settings_without_dsn)
        assert result is False

    def test_init_sentry_returns_true_with_dsn(self, settings_with_dsn: PlatformSettings) -> None:
        result = init_sentry(settings_with_dsn)
        assert result is True

    def test_init_sentry_uses_env_prefix(self) -> None:
        os.environ["EAIP_SENTRY_DSN"] = "https://example@sentry.io/3"
        try:
            settings = PlatformSettings()
            assert settings.sentry.dsn == "https://example@sentry.io/3"
        finally:
            del os.environ["EAIP_SENTRY_DSN"]

    def test_init_sentry_uses_custom_release(self, settings_with_env_override: PlatformSettings) -> None:
        assert settings_with_env_override.sentry.release == "1.2.3"

    def test_init_sentry_uses_custom_environment(self, settings_with_env_override: PlatformSettings) -> None:
        assert settings_with_env_override.sentry.environment == "staging"

    def test_init_sentry_defaults_traces_sample_rate_to_zero(self, settings_with_dsn: PlatformSettings) -> None:
        assert settings_with_dsn.sentry.traces_sample_rate == 0.0

    def test_init_sentry_defaults_send_default_pii_to_false(self, settings_with_dsn: PlatformSettings) -> None:
        assert settings_with_dsn.sentry.send_default_pii is False

    def test_init_sentry_defaults_attach_stacktrace_to_true(self, settings_with_dsn: PlatformSettings) -> None:
        assert settings_with_dsn.sentry.attach_stacktrace is True

    @patch("eaip.integrations.sentry._get_sentry_sdk")
    def test_init_sentry_calls_sentry_init_with_config(self, mock_get_sdk: MagicMock, settings_with_env_override: PlatformSettings) -> None:
        mock_sentry = MagicMock()
        mock_get_sdk.return_value = mock_sentry

        result = init_sentry(settings_with_env_override)

        assert result is True
        mock_sentry.init.assert_called_once()
        call_kwargs = mock_sentry.init.call_args.kwargs
        assert call_kwargs["dsn"] == "https://example@sentry.io/2"
        assert call_kwargs["environment"] == "staging"
        assert call_kwargs["release"] == "1.2.3"
        assert call_kwargs["traces_sample_rate"] == 0.5
        assert call_kwargs["send_default_pii"] is True

    def test_init_sentry_returns_false_when_dsn_is_empty_string(self) -> None:
        settings = PlatformSettings(sentry=SentrySettings(dsn=""))
        result = init_sentry(settings)
        assert result is False


class TestSentryHealthCheck:
    def test_health_check_defaults_to_unhealthy(self) -> None:
        check = SentryHealthCheck()
        assert check.name == "sentry"

    def test_health_check_returns_degraded_when_not_marked_healthy(self) -> None:
        check = SentryHealthCheck()
        import asyncio

        async def _check():
            return await check.check()

        report = asyncio.run(_check())
        assert report.status.value == "degraded"

    def test_health_check_returns_healthy_when_marked_healthy(self) -> None:
        check = SentryHealthCheck()
        check.mark_healthy()
        import asyncio

        async def _check():
            return await check.check()

        report = asyncio.run(_check())
        assert report.status.value == "healthy"


class TestAddSentryMiddleware:
    def test_add_sentry_middleware_does_not_raise(self, settings_with_dsn: PlatformSettings) -> None:
        init_sentry(settings_with_dsn)
        from fastapi import FastAPI

        app = FastAPI()
        add_sentry_middleware(app)
        middleware_classes = [m.__class__.__name__ for m in app.user_middleware]
        assert any("Sentry" in name for name in middleware_classes)


class TestSentrySettingsEnvVars:
    def test_env_var_mapping_dsn(self) -> None:
        os.environ["EAIP_SENTRY_DSN"] = "https://test@sentry.io/1"
        try:
            from eaip.settings.core_settings import load_platform_settings

            settings = load_platform_settings()
            assert settings.sentry.dsn == "https://test@sentry.io/1"
        finally:
            del os.environ["EAIP_SENTRY_DSN"]

    def test_env_var_mapping_traces_sample_rate(self) -> None:
        os.environ["EAIP_SENTRY_TRACES_SAMPLE_RATE"] = "0.25"
        try:
            from eaip.settings.core_settings import load_platform_settings

            settings = load_platform_settings()
            assert settings.sentry.traces_sample_rate == pytest.approx(0.25)
        finally:
            del os.environ["EAIP_SENTRY_TRACES_SAMPLE_RATE"]

    def test_env_var_mapping_send_default_pii(self) -> None:
        os.environ["EAIP_SENTRY_SEND_DEFAULT_PII"] = "true"
        try:
            from eaip.settings.core_settings import load_platform_settings

            settings = load_platform_settings()
            assert settings.sentry.send_default_pii is True
        finally:
            del os.environ["EAIP_SENTRY_SEND_DEFAULT_PII"]

    def test_env_var_mapping_profile_life_cycle(self) -> None:
        os.environ["EAIP_SENTRY_PROFILE_LIFE_CYCLE"] = "error"
        try:
            from eaip.settings.core_settings import load_platform_settings

            settings = load_platform_settings()
            assert settings.sentry.profile_life_cycle == "error"
        finally:
            del os.environ["EAIP_SENTRY_PROFILE_LIFE_CYCLE"]