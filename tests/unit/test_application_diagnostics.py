"""Tests for :mod:`eaip.application.diagnostics`."""

from __future__ import annotations

from unittest.mock import MagicMock

from eaip.application.diagnostics import StartupDiagnostics, StartupDiagnosticsReport
from eaip.application.pipeline import StartupPipeline


class TestStartupDiagnosticsReport:
    def test_default_values(self) -> None:
        report = StartupDiagnosticsReport()
        assert report.startup_duration_seconds == 0.0
        assert report.phase == "created"
        assert report.modules == []
        assert report.module_count == 0
        assert report.plugins == []
        assert report.plugin_count == 0
        assert report.config_validated
        assert report.dependency_graph == {}
        assert report.runtime_version != ""
        assert report.started_at == ""
        assert report.errors == []

    def test_can_create_with_values(self) -> None:
        report = StartupDiagnosticsReport(
            startup_duration_seconds=1.5,
            phase="running",
            modules=["mod1", "mod2"],
            module_count=2,
            plugins=["plug1"],
            plugin_count=1,
            config_validated=True,
            dependency_graph={"module_count": 2, "startup_order": ["mod1", "mod2"]},
            started_at="2026-01-01T00:00:00",
            errors=[],
        )
        assert report.startup_duration_seconds == 1.5
        assert report.module_count == 2


class TestStartupDiagnostics:
    def test_create(self) -> None:
        diag = StartupDiagnostics()
        assert diag is not None

    def test_capture_start_sets_started_at(self) -> None:
        diag = StartupDiagnostics()
        diag.capture_start()
        report = diag.report()
        assert report.started_at != ""

    def test_capture_ready(self) -> None:
        diag = StartupDiagnostics()
        diag.capture_start()
        diag.capture_ready()
        report = diag.report()
        assert report.startup_duration_seconds >= 0.0

    def test_set_config_validated_true(self) -> None:
        diag = StartupDiagnostics()
        diag.set_config_validated(validated=True)
        report = diag.report()
        assert report.config_validated

    def test_set_config_validated_false(self) -> None:
        diag = StartupDiagnostics()
        diag.set_config_validated(validated=False, errors=["invalid config"])
        report = diag.report()
        assert not report.config_validated
        assert "invalid config" in report.errors

    def test_add_error(self) -> None:
        diag = StartupDiagnostics()
        diag.add_error("something went wrong")
        report = diag.report()
        assert "something went wrong" in report.errors

    def test_report_with_no_data(self) -> None:
        diag = StartupDiagnostics()
        report = diag.report()
        assert report.runtime_version != ""
        assert report.module_count == 0

    def test_report_with_pipeline(self) -> None:
        diag = StartupDiagnostics()
        pipeline = StartupPipeline()
        report = diag.report(pipeline=pipeline)
        assert report.phase == "created"

    def test_report_with_kernel(self) -> None:
        diag = StartupDiagnostics()
        kernel_mock = MagicMock()
        kernel_mock.registry.module_names.return_value = ["mod1", "mod2"]
        kernel_mock.host.module_names = ["mod1", "mod2"]
        report = diag.report(kernel=kernel_mock)
        assert report.modules == ["mod1", "mod2"]

    def test_report_with_platform(self) -> None:
        diag = StartupDiagnostics()
        platform_mock = MagicMock()
        plugin1 = MagicMock()
        plugin1.manifest.name = "test-plugin"
        platform_mock.plugins.all.return_value = [plugin1]
        report = diag.report(platform=platform_mock)
        assert report.plugins == ["test-plugin"]

    def test_report_with_all_sources(self) -> None:
        diag = StartupDiagnostics()
        diag.capture_start()

        pipeline = StartupPipeline()
        kernel_mock = MagicMock()
        kernel_mock.registry.module_names.return_value = ["mod1"]
        kernel_mock.host.module_names = ["mod1"]
        kernel_mock.host._loader.all.return_value = []
        platform_mock = MagicMock()
        plugin1 = MagicMock()
        plugin1.manifest.name = "plug1"
        platform_mock.plugins.all.return_value = [plugin1]

        report = diag.report(pipeline=pipeline, platform=platform_mock, kernel=kernel_mock)
        assert report.phase == "created"
        assert report.module_count == 1
        assert report.plugin_count == 1

    def test_multiple_errors_recorded(self) -> None:
        diag = StartupDiagnostics()
        diag.add_error("error 1")
        diag.add_error("error 2")
        report = diag.report()
        assert len(report.errors) == 2
