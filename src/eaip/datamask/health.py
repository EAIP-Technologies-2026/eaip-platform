"""Health check for the data masking module."""

from __future__ import annotations

from eaip.datamask.masking import DataMaskingService
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class DataMaskHealthCheck(HealthCheck):
    name: str = "datamask"

    def __init__(
        self,
        masking_service: DataMaskingService | None = None,
    ) -> None:
        self._masking = masking_service or DataMaskingService()

    async def check(self) -> HealthReport:
        rules = await self._masking.list_rules()
        enabled = [r for r in rules if r.enabled]
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message=f"{len(rules)} masking rule(s), {len(enabled)} enabled",
            details={
                "rules_total": len(rules),
                "rules_enabled": len(enabled),
                "mask_char": self._masking.config.default_mask_char,
                "max_parallel_jobs": self._masking.config.max_parallel_jobs,
            },
        )


__all__ = ["DataMaskHealthCheck"]
