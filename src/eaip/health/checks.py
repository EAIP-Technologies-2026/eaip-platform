"""Health check primitives — models, protocol, helpers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class HealthStatus(StrEnum):
    """Health classification for a single check or an aggregated rollup.

    Ordered from least to most severe via :attr:`numeric`:
    ``HEALTHY < SKIPPED < DEGRADED < UNHEALTHY``.
    """

    HEALTHY = "healthy"
    SKIPPED = "skipped"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

    @property
    def numeric(self) -> int:
        """Higher = worse; useful for sorting/aggregation."""
        return {"healthy": 0, "skipped": 1, "degraded": 2, "unhealthy": 3}[self.value]


class DependencyClass(StrEnum):
    """How strongly a dependency gates platform readiness."""

    CRITICAL = "critical"
    REQUIRED = "required"
    OPTIONAL = "optional"


class HealthReport(BaseModel):
    """Result of a single health check or an aggregated rollup."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    component: str = Field(description="Component that produced this report.")
    status: HealthStatus
    message: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)
    observed_at: datetime = Field(default_factory=utc_now)
    children: tuple[HealthReport, ...] = Field(default=())
    criticality: DependencyClass | None = Field(
        default=None,
        description="Dependency class (critical/required/optional) used for readiness gating.",
    )
    configured: bool | None = Field(
        default=None,
        description="Whether the dependency has configuration required to run.",
    )

    def is_healthy(self) -> bool:
        """Checks if the component is healthy.

        Returns:
            True if status is HEALTHY, False otherwise.
        """
        return self.status is HealthStatus.HEALTHY


@runtime_checkable
class HealthCheck(Protocol):
    """A callable that produces a :class:`HealthReport` on demand.

    Implementations may optionally declare ``criticality`` (a
    :class:`DependencyClass`) and ``configured`` (a bool) attributes; the
    reporter copies them onto the produced :class:`HealthReport` so that
    readiness gating and the dependency table can be derived.
    """

    name: str

    async def check(self) -> HealthReport:
        """Runs the health check.

        Returns:
            A :class:`HealthReport` describing the health of the component.
        """
        ...


def callable_check(name: str, fn: Callable[[], Awaitable[HealthReport]]) -> HealthCheck:
    """Wrap an async callable as a :class:`HealthCheck`."""

    class _AdHoc:
        def __init__(self) -> None:
            """Initializes the AdHoc health check."""
            self.name = name

        async def check(self) -> HealthReport:
            """Runs the health check by calling the wrapped function.

            Returns:
                A :class:`HealthReport` result.
            """
            return await fn()

    return _AdHoc()


__all__ = ["DependencyClass", "HealthCheck", "HealthReport", "HealthStatus", "callable_check"]
