"""Resilience health check - reports circuit breaker, bulkhead, error budget states."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class ResilienceHealthCheck(HealthCheck):
    name: str = "eaip.resilience"

    def __init__(self) -> None:
        self._circuit_breakers: dict[str, object] = {}
        self._bulkheads: dict[str, object] = {}
        self._error_budgets: dict[str, object] = {}

    def register_circuit_breaker(self, cb: object) -> None:
        self._circuit_breakers[getattr(cb, "name", str(id(cb)))] = cb

    def register_bulkhead(self, bh: object) -> None:
        self._bulkheads[getattr(bh, "name", str(id(bh)))] = bh

    def register_error_budget(self, eb: object) -> None:
        self._error_budgets[getattr(eb, "name", str(id(eb)))] = eb

    async def check(self) -> HealthReport:
        open_circuits = 0
        for cb in self._circuit_breakers.values():
            if getattr(cb, "state", None) is not None:
                if str(getattr(cb, "state", "")) in ("open", "half_open"):
                    open_circuits += 1

        exhausted_budgets = 0
        for eb in self._error_budgets.values():
            if getattr(eb, "is_exhausted", False):
                exhausted_budgets += 1

        details: dict[str, object] = {
            "circuit_breakers": len(self._circuit_breakers),
            "open_circuits": open_circuits,
            "bulkheads": len(self._bulkheads),
            "error_budgets": len(self._error_budgets),
            "exhausted_budgets": exhausted_budgets,
        }

        if open_circuits > 0:
            return HealthReport(
                component="resilience",
                status=HealthStatus.DEGRADED,
                message=f"{open_circuits} circuit breaker(s) open",
                details=details,
            )

        if exhausted_budgets > 0:
            return HealthReport(
                component="resilience",
                status=HealthStatus.DEGRADED,
                message=f"{exhausted_budgets} error budget(s) exhausted",
                details=details,
            )

        return HealthReport(
            component="resilience",
            status=HealthStatus.HEALTHY,
            message="All resilience systems nominal",
            details=details,
        )


__all__ = ["ResilienceHealthCheck"]
