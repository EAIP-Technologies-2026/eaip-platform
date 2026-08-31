"""Connector health tracking — monitor availability, latency, and circuit state."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class CircuitState(StrEnum):
    """Circuit breaker states for connector health."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class DegradationLevel(StrEnum):
    """Connector degradation levels."""

    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class ConnectorHealthReport(BaseModel):
    """Detailed health report for a connector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    connector_id: str
    tenant_id: str
    availability: float = Field(ge=0.0, le=1.0, description="Availability 0.0-1.0")
    latency_ms: float = 0.0
    error_rate: float = Field(ge=0.0, le=1.0, description="Error rate 0.0-1.0")
    auth_status: str = "unknown"
    rate_limit_remaining: int = -1
    degradation_level: DegradationLevel = DegradationLevel.NONE
    circuit_state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    last_success_at: Any | None = None
    last_failure_at: Any | None = None
    checked_at: Any = Field(default_factory=utc_now)


class ConnectorHealthTracker:
    """Track and manage connector health metrics.

    Integrates with circuit breaker patterns from Wave 4 resilience.
    """

    def __init__(self) -> None:
        self._health: dict[str, ConnectorHealthReport] = {}
        self._failure_counts: dict[str, int] = {}
        self._circuit_threshold = 5
        self._log = get_logger("eaip.connectors.health_tracker")

    def _key(self, tenant_id: str, connector_id: str) -> str:
        return f"{tenant_id}:{connector_id}"

    async def track_health(self, connector_id: str, tenant_id: str) -> ConnectorHealthReport:
        """Get current health status for a connector."""
        key = self._key(tenant_id, connector_id)
        report = self._health.get(key)
        if report is None:
            report = ConnectorHealthReport(
                connector_id=connector_id,
                tenant_id=tenant_id,
                availability=0.0,
                error_rate=0.0,
                auth_status="not_checked",
            )
            self._health[key] = report
        return report

    async def update_health(
        self,
        connector_id: str,
        tenant_id: str,
        *,
        success: bool = True,
        latency_ms: float = 0.0,
        auth_status: str = "",
        rate_limit_remaining: int = -1,
    ) -> ConnectorHealthReport:
        """Update health metrics after an invocation."""
        key = self._key(tenant_id, connector_id)
        now = utc_now()
        existing = self._health.get(key)

        if success:
            self._failure_counts[key] = 0
            new_report = ConnectorHealthReport(
                connector_id=connector_id,
                tenant_id=tenant_id,
                availability=min(1.0, (existing.availability if existing else 0.0) + 0.1),
                latency_ms=latency_ms,
                error_rate=max(0.0, (existing.error_rate if existing else 0.0) - 0.05),
                auth_status=auth_status or "valid",
                rate_limit_remaining=rate_limit_remaining,
                degradation_level=DegradationLevel.NONE,
                circuit_state=CircuitState.CLOSED,
                consecutive_failures=0,
                last_success_at=now,
                last_failure_at=existing.last_failure_at if existing else None,
                checked_at=now,
            )
        else:
            failures = self._failure_counts.get(key, 0) + 1
            self._failure_counts[key] = failures
            circuit = CircuitState.OPEN if failures >= self._circuit_threshold else CircuitState.CLOSED
            degradation = self._compute_degradation(failures)
            new_report = ConnectorHealthReport(
                connector_id=connector_id,
                tenant_id=tenant_id,
                availability=max(0.0, (existing.availability if existing else 1.0) - 0.1),
                latency_ms=latency_ms,
                error_rate=min(1.0, (existing.error_rate if existing else 0.0) + 0.1),
                auth_status=auth_status or (existing.auth_status if existing else "unknown"),
                rate_limit_remaining=rate_limit_remaining,
                degradation_level=degradation,
                circuit_state=circuit,
                consecutive_failures=failures,
                last_success_at=existing.last_success_at if existing else None,
                last_failure_at=now,
                checked_at=now,
            )

        self._health[key] = new_report
        self._log.info(
            "health.updated",
            connector_id=connector_id,
            success=success,
            circuit=circuit.value,
        )
        return new_report

    async def get_health(self, connector_id: str, tenant_id: str) -> ConnectorHealthReport | None:
        """Get health report for a connector."""
        return self._health.get(self._key(tenant_id, connector_id))

    async def get_unhealthy_connectors(self, tenant_id: str) -> list[ConnectorHealthReport]:
        """Get all degraded or unhealthy connectors for a tenant."""
        return [
            v for v in self._health.values()
            if v.tenant_id == tenant_id
            and v.degradation_level != DegradationLevel.NONE
        ]

    async def is_circuit_open(self, connector_id: str, tenant_id: str) -> bool:
        """Check if the circuit breaker is open for a connector."""
        report = self._health.get(self._key(tenant_id, connector_id))
        if report is None:
            return False
        return report.circuit_state == CircuitState.OPEN

    @staticmethod
    def _compute_degradation(failures: int) -> DegradationLevel:
        if failures >= 10:
            return DegradationLevel.CRITICAL
        if failures >= 7:
            return DegradationLevel.SEVERE
        if failures >= 5:
            return DegradationLevel.MODERATE
        if failures >= 3:
            return DegradationLevel.MINOR
        return DegradationLevel.NONE


__all__ = [
    "CircuitState",
    "ConnectorHealthReport",
    "ConnectorHealthTracker",
    "DegradationLevel",
]
