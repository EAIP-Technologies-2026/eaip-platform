"""Tests for :mod:`eaip.health`."""

from __future__ import annotations

import pytest

from eaip.exceptions.domain import DuplicateRegistrationError
from eaip.health import (
    HealthCheck,
    HealthReport,
    HealthReporter,
    HealthStatus,
    callable_check,
)


def _check(name: str, status: HealthStatus) -> HealthCheck:
    async def _impl() -> HealthReport:
        return HealthReport(component=name, status=status)

    return callable_check(name, _impl)


def _declared_check(name: str, status: HealthStatus, **attrs) -> HealthCheck:
    async def _impl() -> HealthReport:
        return HealthReport(component=name, status=status)

    impl = callable_check(name, _impl)
    for key, value in attrs.items():
        setattr(impl, key, value)
    return impl


@pytest.mark.asyncio
async def test_empty_reporter_is_healthy() -> None:
    r = HealthReporter(name="p")
    report = await r.report()
    assert report.status is HealthStatus.HEALTHY
    assert report.children == ()


@pytest.mark.asyncio
async def test_rollup_picks_worst() -> None:
    r = HealthReporter()
    r.register(_check("a", HealthStatus.HEALTHY))
    r.register(_check("b", HealthStatus.DEGRADED))
    r.register(_check("c", HealthStatus.UNHEALTHY))
    report = await r.report()
    assert report.status is HealthStatus.UNHEALTHY
    assert len(report.children) == 3


@pytest.mark.asyncio
async def test_rollup_orders_skipped_between_healthy_and_degraded() -> None:
    r = HealthReporter()
    r.register(_check("a", HealthStatus.HEALTHY))
    r.register(_check("b", HealthStatus.SKIPPED))
    report = await r.report()
    assert report.status is HealthStatus.SKIPPED


@pytest.mark.asyncio
async def test_failing_check_is_reported_unhealthy() -> None:
    async def boom() -> HealthReport:
        raise RuntimeError("nope")

    r = HealthReporter()
    r.register(callable_check("crashy", boom))
    report = await r.report()
    assert report.status is HealthStatus.UNHEALTHY
    assert report.children[0].component == "crashy"


@pytest.mark.asyncio
async def test_liveness_is_always_healthy() -> None:
    r = HealthReporter()
    r.register(_check("a", HealthStatus.UNHEALTHY))
    report = await r.liveness()
    assert report.status is HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_readiness_fails_on_required_unhealthy() -> None:
    r = HealthReporter()
    r.register(_declared_check("db", HealthStatus.UNHEALTHY))
    report = await r.readiness()
    assert report.status is HealthStatus.UNHEALTHY


@pytest.mark.asyncio
async def test_readiness_ignores_optional_degraded() -> None:
    r = HealthReporter()
    r.register(_declared_check("sentry", HealthStatus.DEGRADED, criticality="optional"))
    r.register(_declared_check("db", HealthStatus.HEALTHY))
    report = await r.readiness()
    assert report.status is HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_readiness_ignores_skipped() -> None:
    r = HealthReporter()
    r.register(_declared_check("db", HealthStatus.SKIPPED, configured=False))
    report = await r.readiness()
    assert report.status is HealthStatus.HEALTHY


def test_duplicate_check_rejected() -> None:
    r = HealthReporter()
    r.register(_check("a", HealthStatus.HEALTHY))
    with pytest.raises(DuplicateRegistrationError):
        r.register(_check("a", HealthStatus.HEALTHY))


def test_status_numeric_ordering() -> None:
    assert (
        HealthStatus.HEALTHY.numeric
        < HealthStatus.SKIPPED.numeric
        < HealthStatus.DEGRADED.numeric
        < HealthStatus.UNHEALTHY.numeric
    )
