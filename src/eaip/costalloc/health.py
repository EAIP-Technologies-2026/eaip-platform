"""Health check for the cost allocation service."""

from __future__ import annotations

from eaip.costalloc.allocator import CostAllocationService
from eaip.health.checks import HealthReport, HealthStatus


class CostAllocHealthCheck:
    name: str = "costalloc"

    def __init__(self, service: CostAllocationService) -> None:
        self._service = service

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            rules = await self._service.list_rules()
            details["rule_count"] = len(rules)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Allocation service unavailable: {exc}",
                details={"error": str(exc)},
            )
        try:
            allocations = await self._service.list_allocations()
            details["allocation_count"] = len(allocations)
        except Exception as exc:
            details["allocation_error"] = str(exc)

        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Cost allocation service healthy",
            details=details,
        )
