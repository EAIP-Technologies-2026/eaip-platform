"""Tests for :mod:`eaip.application.app`."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from eaip.application.app import EAIPApplication
from eaip.application.pipeline import StartupPhase
from eaip.health.checks import HealthReport, HealthStatus
from eaip.platform.platform import Platform
from eaip.runtime.context import RuntimeContext
from eaip.runtime.module import BaseRuntimeModule


class _TestAppModule(BaseRuntimeModule):
    module_name = "test-app-module"

    async def on_start(self, host, ctx: RuntimeContext) -> None:
        pass


class TestEAIPApplicationConstruction:
    def test_create_minimal(self) -> None:
        app = EAIPApplication(configure_logging=False)
        assert app is not None
        assert app.platform is None
        assert app.kernel is None
        assert app.pipeline is None
        assert app.diagnostics is None
        assert app.health_service is None
        assert not app.is_running
        assert app.phase == StartupPhase.CREATED.value

    def test_create_with_custom_logging_setting(self) -> None:
        app = EAIPApplication(configure_logging=False)
        assert not app._configure_logging


class TestEAIPApplicationInitialization:
    def test_initialize_creates_components(self) -> None:
        app = EAIPApplication(configure_logging=False)
        app.initialize()
        assert app.platform is not None
        assert app.kernel is not None
        assert app.pipeline is not None
        assert app.diagnostics is not None
        assert app.health_service is not None
        assert not app.is_running

    def test_initialize_idempotent(self) -> None:
        app = EAIPApplication(configure_logging=False)
        app.initialize()
        platform = app.platform
        app.initialize()
        assert app.platform is platform

    def test_initialize_with_modules(self) -> None:
        module = _TestAppModule()
        app = EAIPApplication(modules=[module], configure_logging=False)
        app.initialize()
        assert app.kernel is not None
        assert "test-app-module" in app.kernel.host.module_names


class TestEAIPApplicationLifecycle:
    @pytest.mark.asyncio
    async def test_start_through_pipeline(self) -> None:
        app = EAIPApplication(configure_logging=False)
        await app.start()
        assert app.is_running
        assert app.phase == StartupPhase.RUNNING.value

    @pytest.mark.asyncio
    async def test_stop_after_start(self) -> None:
        app = EAIPApplication(configure_logging=False)
        await app.start()
        assert app.is_running

        await app.stop()
        assert not app.is_running
        assert app.phase == StartupPhase.STOPPED.value

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self) -> None:
        app = EAIPApplication(configure_logging=False)
        await app.stop()
        assert not app.is_running

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        async with EAIPApplication(configure_logging=False) as app:
            assert app.is_running
        assert not app.is_running

    @pytest.mark.asyncio
    async def test_start_initializes_if_needed(self) -> None:
        app = EAIPApplication(configure_logging=False)
        assert app.pipeline is None
        await app.start()
        assert app.pipeline is not None
        assert app.is_running

    @pytest.mark.asyncio
    async def test_health_before_start(self) -> None:
        app = EAIPApplication(configure_logging=False)
        report = await app.health()
        assert report.status is HealthStatus.DEGRADED
        assert "not initialized" in report.message

    @pytest.mark.asyncio
    async def test_health_after_start(self) -> None:
        app = EAIPApplication(configure_logging=False)
        await app.start()
        report = await app.health()
        assert report is not None
        assert report.component == "application"

    @pytest.mark.asyncio
    async def test_stop_handles_kernel_failure(self) -> None:
        app = EAIPApplication(configure_logging=False)
        await app.start()

        with patch.object(app._kernel, "stop", side_effect=RuntimeError("kernel stop failed")):
            await app.stop()
        assert not app.is_running

    @pytest.mark.asyncio
    async def test_stop_handles_platform_failure(self) -> None:
        app = EAIPApplication(configure_logging=False)
        await app.start()

        async def broken_stop(self: Platform) -> None:
            raise RuntimeError("platform stop failed")

        with patch.object(Platform, "stop", broken_stop):
            await app.stop()
        assert not app.is_running


class TestEAIPApplicationHealth:
    @pytest.mark.asyncio
    async def test_health_returns_report_without_initialization(self) -> None:
        app = EAIPApplication(configure_logging=False)
        report = await app.health()
        assert isinstance(report, HealthReport)

    @pytest.mark.asyncio
    async def test_health_returns_report_after_start(self) -> None:
        app = EAIPApplication(configure_logging=False)
        await app.start()
        report = await app.health()
        assert report.status is not None
        assert report.component == "application"


class TestEAIPApplicationConfigLoading:
    def test_default_config_uses_env(self) -> None:
        app = EAIPApplication(configure_logging=False)
        app.initialize()
        source = app._composition.config_source()
        assert source is not None

    def test_config_with_raw_dict(self) -> None:
        app = EAIPApplication(
            config_raw={"core": {"app_name": "test-app"}},
            configure_logging=False,
        )
        app.initialize()
        assert app.platform is not None
