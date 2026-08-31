"""Health check for the compensation runtime."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.health.checks import HealthReport, HealthStatus

if TYPE_CHECKING:
    from eaip.compensation.service import CompensationService


class CompensationHealthCheck:
    name: str = "compensation"

    def __init__(self, service: CompensationService | None = None) -> None:
        from eaip.compensation.service import CompensationService  # noqa: PLC0415

        self._service = service or CompensationService()

    async def check(self) -> HealthReport:
        error_details: list[str] = []
        plan_count = len(self._service.plans)
        transaction_count = len(self._service.transactions)

        if plan_count == 0:
            error_details.append("No compensation plans registered")

        status = HealthStatus.HEALTHY
        if error_details:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="compensation",
            status=status,
            message="; ".join(error_details)
            if error_details
            else "Compensation runtime is operational",
            details={
                "plans_created": plan_count,
                "transactions_total": transaction_count,
            },
        )


__all__ = ["CompensationHealthCheck"]
