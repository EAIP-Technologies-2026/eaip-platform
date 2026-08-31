"""Health reporter — aggregates per-component reports into a single rollup."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable

from eaip.exceptions.domain import DuplicateRegistrationError
from eaip.health.checks import (
    DependencyClass,
    HealthCheck,
    HealthReport,
    HealthStatus,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


def _criticality(check: HealthCheck) -> DependencyClass:
    return getattr(check, "criticality", DependencyClass.REQUIRED)


def _configured(check: HealthCheck) -> bool:
    return bool(getattr(check, "configured", True))


def _criticality_from_report(report: HealthReport) -> DependencyClass:
    if report.criticality is not None:
        return report.criticality
    return DependencyClass.REQUIRED


class HealthReporter:
    """Registers checks and produces a roll-up :class:`HealthReport`."""

    def __init__(self, *, name: str = "platform") -> None:
        """Initializes a new HealthReporter.

        Args:
            name: The name of the reporter component. Defaults to "platform".
        """
        self._name = name
        self._checks: dict[str, HealthCheck] = {}
        self._log = get_logger("eaip.health.reporter")

    @property
    def name(self) -> str:
        """Returns the name of the reporter.

        Returns:
            The reporter name.
        """
        return self._name

    def register(self, check: HealthCheck) -> None:
        """Register a :class:`HealthCheck`. Names must be unique."""
        if check.name in self._checks:
            raise DuplicateRegistrationError(
                f"health check {check.name!r} already registered",
                context={"name": check.name},
            )
        self._checks[check.name] = check

    def unregister(self, name: str) -> bool:
        """Remove the health check by name.

        Args:
            name: The name of the health check to remove.

        Returns:
            True if the check existed and was removed, False otherwise.
        """
        return self._checks.pop(name, None) is not None

    def registered(self) -> list[str]:
        """Returns the names of all registered health checks.

        Returns:
            A list of check names in alphabetical order.
        """
        return sorted(self._checks)

    async def liveness(self) -> HealthReport:
        """Liveness probe — the process is alive if this is reachable.

        Returns:
            A :class:`HealthReport` that is always ``HEALTHY``.
        """
        return HealthReport(
            component=self._name,
            status=HealthStatus.HEALTHY,
            message="process alive",
            observed_at=utc_now(),
        )

    async def readiness(self) -> HealthReport:
        """Run every registered check and aggregate *readiness*.

        Only critical and required dependencies gate readiness. Optional
        dependencies (and any that are skipped) never fail the platform.

        Returns:
            A :class:`HealthReport` with status ``UNHEALTHY`` only when a
            critical or required dependency is unhealthy.
        """
        if not self._checks:
            return HealthReport(
                component=self._name,
                status=HealthStatus.HEALTHY,
                message="no health checks registered",
                observed_at=utc_now(),
            )
        results = await asyncio.gather(
            *(self._safe_check(c) for c in self._checks.values()),
            return_exceptions=False,
        )
        gating = [r for r in results if _criticality_from_report(r) is not DependencyClass.OPTIONAL]
        if not gating:
            return HealthReport(
                component=self._name,
                status=HealthStatus.HEALTHY,
                message="no critical or required checks registered",
                children=tuple(results),
                observed_at=utc_now(),
            )
        worst = max((c.status for c in gating), key=lambda s: s.numeric)
        return HealthReport(
            component=self._name,
            status=(
                HealthStatus.UNHEALTHY if worst is HealthStatus.UNHEALTHY else HealthStatus.HEALTHY
            ),
            message="ready" if worst is not HealthStatus.UNHEALTHY else "not ready",
            children=tuple(gating),
            observed_at=utc_now(),
        )

    async def report(self) -> HealthReport:
        """Run every registered check concurrently and produce a rollup."""
        if not self._checks:
            return HealthReport(
                component=self._name,
                status=HealthStatus.HEALTHY,
                message="no health checks registered",
                observed_at=utc_now(),
            )
        results = await asyncio.gather(
            *(self._safe_check(c) for c in self._checks.values()),
            return_exceptions=False,
        )
        return self._aggregate(results)

    async def _safe_check(self, check: HealthCheck) -> HealthReport:
        try:
            report = await check.check()
        except BaseException as exc:
            self._log.error("health.check_failed", check=check.name, error=repr(exc))
            report = HealthReport(
                component=check.name,
                status=HealthStatus.UNHEALTHY,
                message=f"check raised: {exc!r}",
            )
        criticality = _criticality(check)
        configured = _configured(check)
        if report.criticality is None:
            report = report.model_copy(update={"criticality": criticality})
        if report.configured is None:
            report = report.model_copy(update={"configured": configured})
        return report

    def _aggregate(self, children: Iterable[HealthReport]) -> HealthReport:
        children_tuple = tuple(children)
        worst = max((c.status for c in children_tuple), key=lambda s: s.numeric)
        message = {
            HealthStatus.HEALTHY: "all checks passed",
            HealthStatus.SKIPPED: "one or more checks skipped",
            HealthStatus.DEGRADED: "one or more checks degraded",
            HealthStatus.UNHEALTHY: "one or more checks unhealthy",
        }[worst]
        return HealthReport(
            component=self._name,
            status=worst,
            message=message,
            children=children_tuple,
        )


__all__ = ["HealthReporter"]
