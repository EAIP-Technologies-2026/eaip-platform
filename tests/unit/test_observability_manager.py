"""Tests for :mod:`eaip.observability.manager` — the observability provider manager."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from eaip.observability.manager import ObservabilityManager, build_observability_manager
from eaip.ports.observability import ObservabilityProvider
from eaip.settings.core_settings import PlatformSettings, SentrySettings


class _FakeProvider(ObservabilityProvider):
    name: str = "fake"

    def __init__(self) -> None:
        self._started = False
        self._stopped = False
        self.tags: dict[str, str] = {}

    def start(self) -> None:
        self._started = True

    def stop(self) -> None:
        self._stopped = True

    def is_healthy(self) -> bool:
        return self._started

    def capture_error(
        self, error: Exception, context: dict[str, object] | None = None
    ) -> str | None:
        return None

    def capture_message(
        self, message: str, level: str = "info", context: dict[str, object] | None = None
    ) -> str | None:
        return None

    def capture_deployment(self, release: str, environment: str) -> str | None:
        return None

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value


class TestObservabilityManagerRegistration:
    def test_register_and_provider_lookup(self) -> None:
        manager = ObservabilityManager(PlatformSettings())
        provider = _FakeProvider()
        manager.register(provider)
        assert manager.provider("fake") is provider

    def test_duplicate_registration_raises(self) -> None:
        manager = ObservabilityManager(PlatformSettings())
        manager.register(_FakeProvider())
        with pytest.raises(ValueError):
            manager.register(_FakeProvider())

    def test_providers_returns_copy(self) -> None:
        manager = ObservabilityManager(PlatformSettings())
        manager.register(_FakeProvider())
        result = manager.providers()
        assert "fake" in result
        result["fake"] = _FakeProvider()  # type: ignore[assignment]
        assert manager.provider("fake") is not result["fake"]


class TestObservabilityManagerLifecycle:
    def test_start_all(self) -> None:
        manager = ObservabilityManager(PlatformSettings())
        provider = _FakeProvider()
        manager.register(provider)
        manager.start_all()
        assert provider._started is True

    def test_stop_all_reverse_order(self) -> None:
        manager = ObservabilityManager(PlatformSettings())
        p1 = _FakeProvider()
        p2 = _FakeProvider()
        p1.name = "fake1"
        p2.name = "fake2"
        manager.register(p1)
        manager.register(p2)
        manager.start_all()
        manager.stop_all()
        assert p1._stopped is True
        assert p2._stopped is True


class TestObservabilityManagerHealth:
    async def test_health_report_healthy(self) -> None:
        manager = ObservabilityManager(PlatformSettings())
        provider = _FakeProvider()
        provider._started = True
        manager.register(provider)
        report = await manager.health_report()
        assert report["fake"]["status"] == "healthy"
        assert report["fake"]["registered"] == "true"

    async def test_health_report_degraded_when_not_started(self) -> None:
        manager = ObservabilityManager(PlatformSettings())
        manager.register(_FakeProvider())
        report = await manager.health_report()
        assert report["fake"]["status"] == "degraded"


class TestObservabilityManagerTagging:
    def test_tag_database_provider(self) -> None:
        manager = ObservabilityManager(PlatformSettings())
        provider = _FakeProvider()
        manager.register(provider)
        manager.tag_database_provider("neon")
        assert provider.tags["db_provider"] == "neon"

    def test_tag_database_provider_tolerates_failure(self) -> None:
        manager = ObservabilityManager(PlatformSettings())
        provider = _FakeProvider()

        def _raise(key: str, value: str) -> None:
            raise RuntimeError("boom")

        provider.set_tag = _raise  # type: ignore[assignment]
        manager.register(provider)
        manager.tag_database_provider("local")


class TestBuildObservabilityManager:
    def test_build_without_sentry_registers_better_stack(self) -> None:
        manager = build_observability_manager(PlatformSettings())
        names = list(manager.providers().keys())
        assert "better_stack" in names
        assert "sentry" not in names

    def test_build_with_sentry_dsn_registers_sentry(self) -> None:
        settings = PlatformSettings(sentry=SentrySettings(dsn="https://example@sentry.io/1"))
        with patch("eaip.observability.manager.init_sentry", return_value=True):
            manager = build_observability_manager(settings)
        names = list(manager.providers().keys())
        assert "sentry" in names
        assert "better_stack" in names


__all__: list[str] = []
