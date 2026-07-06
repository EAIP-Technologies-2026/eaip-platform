"""Tests for :mod:`eaip.application.health`."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eaip.application.diagnostics import StartupDiagnostics
from eaip.application.health import ApplicationHealthService
from eaip.application.pipeline import StartupPipeline
from eaip.health.checks import HealthReport, HealthStatus


class _HealthTestModule:
    """A minimal module-like object that passes RuntimeHealthCheck."""

    def __init__(self, name: str) -> None:
        self.name = name

    async def check_health(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="test module healthy",
        )


@pytest.fixture
def platform_mock() -> MagicMock:
    p = MagicMock()
    p.health.report = AsyncMock(
        return_value=HealthReport(
            component="platform",
            status=HealthStatus.HEALTHY,
            message="all good",
        )
    )
    plugin1 = MagicMock()
    plugin1.manifest.name = "p1"
    plugin1.manifest.version = "1.0"
    p.plugins.all.return_value = [plugin1]
    return p


@pytest.fixture
def kernel_mock() -> MagicMock:
    k = MagicMock()
    k.is_running = True
    k.registry.module_names.return_value = ["mod1", "mod2"]
    k.host.get_module.side_effect = lambda name: _HealthTestModule(name=name)
    return k


@pytest.fixture
def health_service(platform_mock: MagicMock, kernel_mock: MagicMock) -> ApplicationHealthService:
    pipeline = StartupPipeline()
    diagnostics = StartupDiagnostics()
    return ApplicationHealthService(
        platform=platform_mock,
        kernel=kernel_mock,
        pipeline=pipeline,
        diagnostics=diagnostics,
    )


class TestApplicationHealthServiceConstruction:
    def test_create_with_minimal_args(self, platform_mock: MagicMock) -> None:
        service = ApplicationHealthService(platform=platform_mock)
        assert service is not None


class TestApplicationHealthServicePlatformHealth:
    @pytest.mark.asyncio
    async def test_platform_health_delegates(
        self,
        health_service: ApplicationHealthService,
    ) -> None:
        report = await health_service.platform_health()
        assert report.status is HealthStatus.HEALTHY
        assert report.component == "platform"

    @pytest.mark.asyncio
    async def test_platform_health_handles_exception(self, platform_mock: MagicMock) -> None:
        platform_mock.health.report = AsyncMock(side_effect=RuntimeError("broken"))
        service = ApplicationHealthService(platform=platform_mock)
        report = await service.platform_health()
        assert report.status is HealthStatus.UNHEALTHY


class TestApplicationHealthServiceRuntimeHealth:
    @pytest.mark.asyncio
    async def test_runtime_health_healthy(self, health_service: ApplicationHealthService) -> None:
        report = await health_service.runtime_health()
        assert report.status is HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_runtime_health_without_kernel(self, platform_mock: MagicMock) -> None:
        service = ApplicationHealthService(platform=platform_mock)
        report = await service.runtime_health()
        assert report.status is HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_runtime_health_not_running(
        self,
        kernel_mock: MagicMock,
        platform_mock: MagicMock,
    ) -> None:
        kernel_mock.is_running = False
        service = ApplicationHealthService(platform=platform_mock, kernel=kernel_mock)
        report = await service.runtime_health()
        assert report.status is HealthStatus.DEGRADED


class TestApplicationHealthServiceModuleHealth:
    @pytest.mark.asyncio
    async def test_module_health_returns_reports(
        self,
        health_service: ApplicationHealthService,
    ) -> None:
        reports = await health_service.module_health()
        assert len(reports) > 0

    @pytest.mark.asyncio
    async def test_module_health_specific_module(
        self,
        health_service: ApplicationHealthService,
    ) -> None:
        reports = await health_service.module_health(module_name="mod1")
        assert all(r.component == "mod1" for r in reports)

    @pytest.mark.asyncio
    async def test_module_health_without_kernel(self, platform_mock: MagicMock) -> None:
        service = ApplicationHealthService(platform=platform_mock)
        reports = await service.module_health()
        assert len(reports) == 1
        assert reports[0].status is HealthStatus.DEGRADED


class TestApplicationHealthServicePluginHealth:
    @pytest.mark.asyncio
    async def test_plugin_health_returns_reports(
        self,
        health_service: ApplicationHealthService,
    ) -> None:
        reports = await health_service.plugin_health()
        assert len(reports) == 1
        assert reports[0].component == "plugin:p1"
        assert reports[0].status is HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_plugin_health_handles_exception(self, platform_mock: MagicMock) -> None:
        platform_mock.plugins.all.side_effect = RuntimeError("broken")
        service = ApplicationHealthService(platform=platform_mock)
        reports = await service.plugin_health()
        assert len(reports) == 1
        assert reports[0].status is HealthStatus.UNHEALTHY


class TestApplicationHealthServiceStartupDiagnostics:
    @pytest.mark.asyncio
    async def test_startup_diagnostics_returns_report(
        self,
        health_service: ApplicationHealthService,
    ) -> None:
        report = await health_service.startup_diagnostics()
        assert report.component == "startup"

    @pytest.mark.asyncio
    async def test_startup_diagnostics_without_diag(self, platform_mock: MagicMock) -> None:
        service = ApplicationHealthService(platform=platform_mock)
        report = await service.startup_diagnostics()
        assert report.status is HealthStatus.DEGRADED


class TestApplicationHealthServiceAggregated:
    @pytest.mark.asyncio
    async def test_report_aggregates_all_sources(
        self,
        health_service: ApplicationHealthService,
    ) -> None:
        report = await health_service.report()
        assert report.component == "application"
        assert report.status is HealthStatus.HEALTHY
        assert len(report.children) > 0

    @pytest.mark.asyncio
    async def test_report_with_degraded_child(self, platform_mock: MagicMock) -> None:
        platform_mock.health.report = AsyncMock(
            return_value=HealthReport(
                component="platform",
                status=HealthStatus.DEGRADED,
                message="degraded",
            )
        )
        service = ApplicationHealthService(platform=platform_mock)
        report = await service.report()
        assert report.status is HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_report_with_no_sources(self) -> None:
        platform_mock = MagicMock()
        platform_mock.health.report = AsyncMock(
            return_value=HealthReport(
                component="platform",
                status=HealthStatus.HEALTHY,
                message="no checks",
            )
        )
        service = ApplicationHealthService(platform=platform_mock)
        report = await service.report()
        assert report.status is not None
