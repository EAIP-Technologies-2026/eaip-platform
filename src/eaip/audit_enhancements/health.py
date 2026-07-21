"""Health check for the audit enhancements subsystem."""

from __future__ import annotations

from eaip.audit_enhancements.service import AuditEnhancementService
from eaip.health.checks import HealthReport, HealthStatus


class AuditEnhancementHealthCheck:
    name: str = "audit_enhancements"

    def __init__(self, service: AuditEnhancementService) -> None:
        self._service = service

    async def check(self) -> HealthReport:
        error_details: list[str] = []
        config = self._service.config

        correlation_rules = len(self._service.list_correlation_rules())
        enrichment_rules = len(self._service.list_enrichment_rules())
        aggregation_rules = len(self._service.list_aggregation_rules())
        alert_rules = len(self._service.list_alert_rules())
        stream_configs = len(self._service.list_stream_configs())

        if not config.enabled:
            error_details.append("Audit enhancements are disabled")

        status = HealthStatus.HEALTHY
        if error_details:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="audit_enhancements",
            status=status,
            message="; ".join(error_details)
            if error_details
            else "Audit enhancements subsystem is operational",
            details={
                "enabled": config.enabled,
                "correlation_rules": correlation_rules,
                "enrichment_rules": enrichment_rules,
                "aggregation_rules": aggregation_rules,
                "alert_rules": alert_rules,
                "stream_configs": stream_configs,
            },
        )


__all__ = ["AuditEnhancementHealthCheck"]
