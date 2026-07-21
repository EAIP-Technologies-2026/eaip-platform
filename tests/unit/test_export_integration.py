"""Tests for the export runtime module integration."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.export.delivery import DeliveryService
from eaip.export.engine import ExportEngine
from eaip.export.health import ExportHealthCheck
from eaip.export.integration import ExportRuntimeModule
from eaip.export.models import ExportConfig, ReportDefinition
from eaip.export.scheduler import ExportScheduler


class TestExportRuntimeModule:
    def test_default_construction(self) -> None:
        module = ExportRuntimeModule()
        assert module.name == "export"
        assert isinstance(module.engine, ExportEngine)
        assert isinstance(module.scheduler, ExportScheduler)
        assert isinstance(module.delivery, DeliveryService)

    def test_custom_construction(self) -> None:
        config = ExportConfig(default_format="xlsx")
        engine = ExportEngine(config=config)
        scheduler = ExportScheduler()
        delivery = DeliveryService()
        module = ExportRuntimeModule(
            config=config,
            engine=engine,
            scheduler=scheduler,
            delivery=delivery,
        )
        assert module.engine is engine
        assert module.scheduler is scheduler
        assert module.delivery is delivery
        assert module.engine.config.default_format == "xlsx"

    @pytest.mark.asyncio
    async def test_start_registers_capability_and_health(self) -> None:
        module = ExportRuntimeModule()

        mock_kernel = MagicMock()
        mock_platform = MagicMock()
        mock_capabilities = MagicMock()
        mock_health = MagicMock()
        mock_platform.capabilities = mock_capabilities
        mock_platform.health = mock_health
        mock_kernel.platform = mock_platform

        await module.start(mock_kernel)

        mock_capabilities.register.assert_called_once()
        mock_health.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_does_not_raise(self) -> None:
        module = ExportRuntimeModule()
        mock_kernel = MagicMock()
        await module.stop(mock_kernel)

    def test_name_property(self) -> None:
        module = ExportRuntimeModule()
        assert module.name == "export"


class TestExportHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy_when_reports_exist(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        check = ExportHealthCheck(engine=engine)
        report = await check.check()
        assert report.component == "export"

    @pytest.mark.asyncio
    async def test_degraded_when_no_reports(self) -> None:
        engine = ExportEngine()
        check = ExportHealthCheck(engine=engine)
        report = await check.check()
        assert "No report definitions registered" in report.message

    def test_name_property(self) -> None:
        engine = ExportEngine()
        check = ExportHealthCheck(engine=engine)
        assert check.name == "export"
