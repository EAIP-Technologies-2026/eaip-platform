from __future__ import annotations

from eaip.observability.health import ObservabilityHealthCheck
from eaip.observability.integration import ObservabilityRuntimeModule
from eaip.observability.models import ObservabilityConfig


class TestObservabilityRuntimeModule:
    def test_module_name(self) -> None:
        module = ObservabilityRuntimeModule()
        assert module.name == "observability"

    def test_default_config(self) -> None:
        module = ObservabilityRuntimeModule()
        assert module._config.evaluation_interval_seconds == 60

    def test_custom_config(self) -> None:
        config = ObservabilityConfig(evaluation_interval_seconds=120)
        module = ObservabilityRuntimeModule(config=config)
        assert module._config.evaluation_interval_seconds == 120

    def test_dashboard_service_property(self) -> None:
        module = ObservabilityRuntimeModule()
        assert module.dashboard_service is not None
        assert module.dashboard_service.name == "observability.dashboards"

    def test_alert_service_property(self) -> None:
        module = ObservabilityRuntimeModule()
        assert module.alert_service is not None
        assert module.alert_service.name == "observability.alerting"

    def test_sli_service_property(self) -> None:
        module = ObservabilityRuntimeModule()
        assert module.sli_service is not None
        assert module.sli_service.name == "observability.slo"

    def test_services_share_config(self) -> None:
        config = ObservabilityConfig(evaluation_interval_seconds=300)
        module = ObservabilityRuntimeModule(config=config)
        assert module.dashboard_service.config.evaluation_interval_seconds == 300
        assert module.alert_service.config.evaluation_interval_seconds == 300
        assert module.sli_service.config.evaluation_interval_seconds == 300


class TestObservabilityHealthCheck:
    async def test_healthy(self) -> None:
        check = ObservabilityHealthCheck(dashboards_count=1, alert_rules_count=2, slos_count=1)
        report = await check.check()
        assert report.status.value == "healthy"
        assert report.details["dashboards_total"] == 1
        assert report.details["alert_rules_total"] == 2
        assert report.details["slos_total"] == 1

    async def test_degraded_empty(self) -> None:
        check = ObservabilityHealthCheck()
        report = await check.check()
        assert report.status.value == "degraded"
        assert "No dashboards configured" in report.message

    async def test_degraded_no_alerts(self) -> None:
        check = ObservabilityHealthCheck(dashboards_count=1, alert_rules_count=0, slos_count=1)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "No alert rules configured" in report.message
