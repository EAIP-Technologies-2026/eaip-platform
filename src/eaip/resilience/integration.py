"""Runtime integration — ResilienceRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from eaip.resilience.bulkhead import Bulkhead, BulkheadConfig
from eaip.resilience.error_budget import ErrorBudget, ErrorBudgetConfig
from eaip.resilience.health import ResilienceHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ResilienceRuntimeModule:
    """RuntimeModule that registers resilience components with the kernel."""

    name: str = "resilience"

    def __init__(
        self,
        event_bus: Any = None,
        meter: Any = None,
    ) -> None:
        self._event_bus = event_bus
        self._meter = meter
        self._health_check = ResilienceHealthCheck()
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._bulkheads: dict[str, Bulkhead] = {}
        self._error_budgets: dict[str, ErrorBudget] = {}
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.resilience.integration")

    def create_circuit_breaker(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> CircuitBreaker:
        if name not in self._circuit_breakers:
            cb = CircuitBreaker(
                name, config,
                event_bus=self._event_bus, meter=self._meter,
            )
            self._circuit_breakers[name] = cb
            self._health_check.register_circuit_breaker(cb)
        return self._circuit_breakers[name]

    def create_bulkhead(
        self,
        name: str,
        config: BulkheadConfig | None = None,
    ) -> Bulkhead:
        if name not in self._bulkheads:
            bh = Bulkhead(name, config, meter=self._meter)
            self._bulkheads[name] = bh
            self._health_check.register_bulkhead(bh)
        return self._bulkheads[name]

    def create_error_budget(
        self,
        name: str,
        config: ErrorBudgetConfig | None = None,
    ) -> ErrorBudget:
        if name not in self._error_budgets:
            eb = ErrorBudget(name, config, event_bus=self._event_bus, meter=self._meter)
            self._error_budgets[name] = eb
            self._health_check.register_error_budget(eb)
        return self._error_budgets[name]

    def get_circuit_breaker(self, name: str) -> CircuitBreaker | None:
        return self._circuit_breakers.get(name)

    def get_bulkhead(self, name: str) -> Bulkhead | None:
        return self._bulkheads.get(name)

    def get_error_budget(self, name: str) -> ErrorBudget | None:
        return self._error_budgets.get(name)

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("resilience.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(Capability(
            name="resilience:framework",
            title="Resilience Framework",
            status=CapabilityStatus.ENABLED,
            tags=("resilience", "circuit-breaker", "bulkhead"),
        ))

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "resilience.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("resilience.module.stop")


__all__ = ["ResilienceRuntimeModule"]
