"""Health check for the contract management service."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ContractHealthCheck:
    name: str = "contract"

    def __init__(self, contract_count: int = 0, active_count: int = 0) -> None:
        self._contract_count = contract_count
        self._active_count = active_count

    async def check(self) -> HealthReport:
        details = {
            "contract_count": self._contract_count,
            "active_count": self._active_count,
        }
        status = HealthStatus.HEALTHY
        message = "Contract management service is operational"

        if self._contract_count == 0:
            status = HealthStatus.DEGRADED
            message = "No contracts registered"

        return HealthReport(
            component="contract",
            status=status,
            message=message,
            details=details,
        )


__all__ = ["ContractHealthCheck"]
