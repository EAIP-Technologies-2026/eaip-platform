"""Health check for the data sampling module."""

from __future__ import annotations

from eaip.datasample.sampler import DataSamplingService
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class DataSampleHealthCheck(HealthCheck):
    name: str = "datasample"

    def __init__(
        self,
        sampler: DataSamplingService | None = None,
    ) -> None:
        self._sampler = sampler or DataSamplingService()

    async def check(self) -> HealthReport:
        definitions = await self._sampler.list_definitions()
        enabled = [d for d in definitions if d.enabled]
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message=f"{len(definitions)} definition(s), {len(enabled)} enabled",
            details={
                "definitions_total": len(definitions),
                "definitions_enabled": len(enabled),
                "max_sample_size": self._sampler.config.max_sample_size,
                "default_strategy": self._sampler.config.default_strategy.value,
            },
        )


__all__ = ["DataSampleHealthCheck"]
