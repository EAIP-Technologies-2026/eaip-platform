from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.observability.alerting import AlertService
from eaip.observability.dashboards import DashboardService
from eaip.observability.health import ObservabilityHealthCheck
from eaip.observability.models import ObservabilityConfig
from eaip.observability.slo import SliService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ObservabilityRuntimeModule:
    name: str = "observability"

    def __init__(
        self,
        config: ObservabilityConfig | None = None,
        dashboard_service: DashboardService | None = None,
        alert_service: AlertService | None = None,
        sli_service: SliService | None = None,
    ) -> None:
        self._config = config or ObservabilityConfig()
        self._dashboard_service = dashboard_service or DashboardService(config=self._config)
        self._alert_service = alert_service or AlertService(config=self._config)
        self._sli_service = sli_service or SliService(config=self._config)
        self._log = get_logger("eaip.observability.integration")

    @property
    def dashboard_service(self) -> DashboardService:
        return self._dashboard_service

    @property
    def alert_service(self) -> AlertService:
        return self._alert_service

    @property
    def sli_service(self) -> SliService:
        return self._sli_service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("observability.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.observability",
            title="Observability Extensions",
            description="Custom dashboards, alert rules, notification channels, and service level objectives (SLOs)",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("observability", "dashboards", "alerting", "slo", "monitoring"),
        )
        platform.capabilities.register(capability)
        platform.health.register(
            ObservabilityHealthCheck(
                dashboards_count=len(self._dashboard_service.list_dashboards()),
                alert_rules_count=len(self._alert_service.list_rules()),
                slos_count=len(self._sli_service.list_slos()),
            ),
        )
        self._log.info("observability.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("observability.module.stopping")


__all__ = ["ObservabilityRuntimeModule"]
