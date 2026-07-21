"""Tests for :mod:`eaip.healthrpt.reporter`."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from eaip.health.checks import HealthStatus
from eaip.healthrpt.exceptions import ComponentNotFoundError, ReporterError
from eaip.healthrpt.models import (
    ComponentSummary,
    HealthReport,
    ReporterConfig,
    SLAResult,
)
from eaip.healthrpt.reporter import HealthReporter
from eaip.shared.time import utc_now


class TestHealthReporter:
    @pytest.fixture
    def reporter(self) -> HealthReporter:
        return HealthReporter()

    @pytest.fixture
    def sample_component(self) -> ComponentSummary:
        return ComponentSummary(
            component_id="comp1",
            component_name="API Gateway",
            status=HealthStatus.HEALTHY,
        )

    class TestRegisterComponent:
        async def test_register(
            self, reporter: HealthReporter, sample_component: ComponentSummary
        ) -> None:
            result = await reporter.register_component(sample_component)
            assert result.component_id == "comp1"

        async def test_list(
            self, reporter: HealthReporter, sample_component: ComponentSummary
        ) -> None:
            await reporter.register_component(sample_component)
            components = await reporter.list_components()
            assert len(components) == 1

    class TestUnregisterComponent:
        async def test_unregister(
            self, reporter: HealthReporter, sample_component: ComponentSummary
        ) -> None:
            await reporter.register_component(sample_component)
            await reporter.unregister_component("comp1")
            components = await reporter.list_components()
            assert len(components) == 0

        async def test_unregister_not_found(self, reporter: HealthReporter) -> None:
            with pytest.raises(ComponentNotFoundError):
                await reporter.unregister_component("nonexistent")

    class TestRecordCheck:
        async def test_record(
            self, reporter: HealthReporter, sample_component: ComponentSummary
        ) -> None:
            await reporter.register_component(sample_component)
            updated = await reporter.record_check("comp1", HealthStatus.HEALTHY)
            assert updated.status == HealthStatus.HEALTHY
            assert updated.check_count == 1
            assert updated.pass_count == 1

        async def test_record_not_found(self, reporter: HealthReporter) -> None:
            with pytest.raises(ComponentNotFoundError):
                await reporter.record_check("nonexistent", HealthStatus.HEALTHY)

        async def test_record_tracks_status_changes(
            self, reporter: HealthReporter, sample_component: ComponentSummary
        ) -> None:
            await reporter.register_component(sample_component)
            await reporter.record_check("comp1", HealthStatus.UNHEALTHY)
            updated = await reporter.record_check("comp1", HealthStatus.HEALTHY)
            assert updated.status == HealthStatus.HEALTHY
            assert updated.check_count == 2
            assert updated.pass_count == 1
            assert updated.fail_count == 1

    class TestGenerateReport:
        async def test_generate(
            self, reporter: HealthReporter, sample_component: ComponentSummary
        ) -> None:
            await reporter.register_component(sample_component)
            await reporter.record_check("comp1", HealthStatus.HEALTHY)
            now = utc_now()
            report = await reporter.generate_report(
                period_start=now - timedelta(hours=1),
                period_end=now,
            )
            assert report.overall_status == HealthStatus.HEALTHY
            assert len(report.component_summaries) == 1

        async def test_generate_multiple_components(self, reporter: HealthReporter) -> None:
            c1 = ComponentSummary(
                component_id="c1", component_name="API", status=HealthStatus.HEALTHY
            )
            c2 = ComponentSummary(
                component_id="c2", component_name="DB", status=HealthStatus.DEGRADED
            )
            await reporter.register_component(c1)
            await reporter.register_component(c2)
            await reporter.record_check("c1", HealthStatus.HEALTHY)
            await reporter.record_check("c2", HealthStatus.DEGRADED)
            now = utc_now()
            report = await reporter.generate_report(
                period_start=now - timedelta(hours=1),
                period_end=now,
            )
            assert len(report.component_summaries) == 2

    class TestGetSLARreport:
        async def test_get_sla(
            self, reporter: HealthReporter, sample_component: ComponentSummary
        ) -> None:
            await reporter.register_component(sample_component)
            sla = await reporter.get_sla_report("comp1")
            assert sla.component_id == "comp1"
            assert sla.compliant is True

        async def test_sla_not_found(self, reporter: HealthReporter) -> None:
            with pytest.raises(ComponentNotFoundError):
                await reporter.get_sla_report("nonexistent")

    class TestGetTrend:
        async def test_trend(
            self, reporter: HealthReporter, sample_component: ComponentSummary
        ) -> None:
            await reporter.register_component(sample_component)
            await reporter.record_check("comp1", HealthStatus.HEALTHY)
            trend = await reporter.get_trend("comp1")
            assert len(trend) == 1

        async def test_trend_not_found(self, reporter: HealthReporter) -> None:
            with pytest.raises(ComponentNotFoundError):
                await reporter.get_trend("nonexistent")

    class TestGetLatestReport:
        async def test_no_reports(self, reporter: HealthReporter) -> None:
            report = await reporter.get_latest_report()
            assert report is None

        async def test_latest(
            self, reporter: HealthReporter, sample_component: ComponentSummary
        ) -> None:
            await reporter.register_component(sample_component)
            now = utc_now()
            await reporter.generate_report(
                period_start=now - timedelta(hours=1),
                period_end=now,
            )
            report = await reporter.get_latest_report()
            assert report is not None

    class TestGetReportHistory:
        async def test_history(
            self, reporter: HealthReporter, sample_component: ComponentSummary
        ) -> None:
            await reporter.register_component(sample_component)
            now = utc_now()
            await reporter.generate_report(
                period_start=now - timedelta(hours=2),
                period_end=now - timedelta(hours=1),
            )
            await reporter.generate_report(
                period_start=now - timedelta(hours=1),
                period_end=now,
            )
            history = await reporter.get_report_history()
            assert len(history) == 2

    class TestConfig:
        def test_default_config(self) -> None:
            r = HealthReporter()
            assert r.config.report_interval_hours == 24
            assert r.config.sla_target_percentage == 99.9

        def test_custom_config(self) -> None:
            config = ReporterConfig(report_interval_hours=12, sla_target_percentage=99.5)
            r = HealthReporter(config=config)
            assert r.config.report_interval_hours == 12
            assert r.config.sla_target_percentage == 99.5
