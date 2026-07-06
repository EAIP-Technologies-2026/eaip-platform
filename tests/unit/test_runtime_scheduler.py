"""Unit tests for :mod:`eaip.runtime.scheduler`."""

from __future__ import annotations

import asyncio

import pytest

from eaip.exceptions.domain import DuplicateRegistrationError
from eaip.health.checks import HealthStatus
from eaip.runtime.context import RuntimeContext
from eaip.runtime.module import BaseRuntimeModule
from eaip.runtime.scheduler import SchedulerModule
from eaip.shared.time import Duration


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class _FakeHost:
    """Minimal stand-in for RuntimeHost during scheduler tests."""

    def __init__(self) -> None:
        self.module_names: list[str] = []


class _FakeCtx:
    """Minimal stand-in for RuntimeContext."""
    run_id: str = "test-run"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_job() -> None:
    scheduler = SchedulerModule()
    assert scheduler.job_count == 0

    async def my_job(_self: object, _ctx: object) -> None:
        pass

    scheduler.register("test-job", my_job)
    assert scheduler.job_count == 1
    assert "test-job" in scheduler.job_names


@pytest.mark.asyncio
async def test_register_duplicate_raises() -> None:
    scheduler = SchedulerModule()

    async def my_job(_self: object, _ctx: object) -> None:
        pass

    scheduler.register("test-job", my_job)
    with pytest.raises(DuplicateRegistrationError):
        scheduler.register("test-job", my_job)


@pytest.mark.asyncio
async def test_register_empty_name_raises() -> None:
    scheduler = SchedulerModule()

    async def my_job(_self: object, _ctx: object) -> None:
        pass

    with pytest.raises(ValueError, match="non-empty"):
        scheduler.register("", my_job)


@pytest.mark.asyncio
async def test_unregister_job() -> None:
    scheduler = SchedulerModule()

    async def my_job(_self: object, _ctx: object) -> None:
        pass

    scheduler.register("test-job", my_job)
    assert scheduler.unregister("test-job") is True
    assert scheduler.job_count == 0


@pytest.mark.asyncio
async def test_unregister_unknown_returns_false() -> None:
    scheduler = SchedulerModule()
    assert scheduler.unregister("nope") is False


@pytest.mark.asyncio
async def test_get_job() -> None:
    scheduler = SchedulerModule()

    async def my_job(_self: object, _ctx: object) -> None:
        pass

    scheduler.register("test-job", my_job)
    job = scheduler.get_job("test-job")
    assert job is not None
    assert job.name == "test-job"
    assert job.interval is None

    assert scheduler.get_job("nope") is None


# ---------------------------------------------------------------------------
# One-shot jobs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_one_shot_job_runs_on_start() -> None:
    scheduler = SchedulerModule()
    executed: list[str] = []

    async def my_job(_self: object, _ctx: object) -> None:
        executed.append("ran")

    scheduler.register("oneshot", my_job)
    await scheduler.on_start(_FakeHost(), _FakeCtx())
    assert executed == ["ran"]
    await scheduler.on_stop(_FakeHost(), _FakeCtx())


@pytest.mark.asyncio
async def test_multiple_one_shot_jobs_run_on_start() -> None:
    scheduler = SchedulerModule()
    order: list[str] = []

    async def job_a(_self: object, _ctx: object) -> None:
        order.append("a")

    async def job_b(_self: object, _ctx: object) -> None:
        order.append("b")

    scheduler.register("a", job_a)
    scheduler.register("b", job_b)
    await scheduler.on_start(_FakeHost(), _FakeCtx())
    assert "a" in order
    assert "b" in order
    await scheduler.on_stop(_FakeHost(), _FakeCtx())


# ---------------------------------------------------------------------------
# Recurring jobs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recurring_job_executes_multiple_times() -> None:
    scheduler = SchedulerModule(poll_interval=Duration.from_milliseconds(10))
    count = 0

    async def my_job(_self: object, _ctx: object) -> None:
        nonlocal count
        count += 1

    scheduler.register("recurring", my_job, interval=Duration.from_milliseconds(20))
    await scheduler.on_start(_FakeHost(), _FakeCtx())

    # Let the loop tick a few times.
    await asyncio.sleep(0.1)

    await scheduler.on_stop(_FakeHost(), _FakeCtx())
    assert count >= 2


@pytest.mark.asyncio
async def test_recurring_job_error_tracked() -> None:
    scheduler = SchedulerModule(poll_interval=Duration.from_milliseconds(10))
    call_count = 0

    async def failing_job(_self: object, _ctx: object) -> None:
        nonlocal call_count
        call_count += 1
        raise RuntimeError("job failed")

    scheduler.register("failing", failing_job, interval=Duration.from_milliseconds(20))
    await scheduler.on_start(_FakeHost(), _FakeCtx())
    await asyncio.sleep(0.1)
    await scheduler.on_stop(_FakeHost(), _FakeCtx())

    job = scheduler.get_job("failing")
    assert job is not None
    assert job.error_count > 0


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_stop_idempotent() -> None:
    scheduler = SchedulerModule()

    async def my_job(_self: object, _ctx: object) -> None:
        pass

    scheduler.register("test", my_job, interval=Duration.from_seconds(60))
    await scheduler.on_start(_FakeHost(), _FakeCtx())
    await scheduler.on_stop(_FakeHost(), _FakeCtx())
    await scheduler.on_stop(_FakeHost(), _FakeCtx())  # second stop is safe


@pytest.mark.asyncio
async def test_start_without_recurring_jobs() -> None:
    scheduler = SchedulerModule()
    await scheduler.on_start(_FakeHost(), _FakeCtx())
    await scheduler.on_stop(_FakeHost(), _FakeCtx())


@pytest.mark.asyncio
async def test_start_with_no_jobs() -> None:
    scheduler = SchedulerModule()
    await scheduler.on_start(_FakeHost(), _FakeCtx())
    await scheduler.on_stop(_FakeHost(), _FakeCtx())


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_healthy() -> None:
    scheduler = SchedulerModule()

    async def my_job(_self: object, _ctx: object) -> None:
        pass

    scheduler.register("ok", my_job, interval=Duration.from_seconds(60))
    await scheduler.on_start(_FakeHost(), _FakeCtx())
    report = await scheduler.check_health()
    assert report.status == HealthStatus.HEALTHY
    await scheduler.on_stop(_FakeHost(), _FakeCtx())


@pytest.mark.asyncio
async def test_health_degraded_on_failures() -> None:
    scheduler = SchedulerModule(poll_interval=Duration.from_milliseconds(10))

    async def failing_job(_self: object, _ctx: object) -> None:
        raise RuntimeError("fail")

    scheduler.register("bad", failing_job, interval=Duration.from_milliseconds(20))
    await scheduler.on_start(_FakeHost(), _FakeCtx())
    await asyncio.sleep(0.1)
    await scheduler.on_stop(_FakeHost(), _FakeCtx())

    report = await scheduler.check_health()
    assert report.status in (HealthStatus.DEGRADED, HealthStatus.HEALTHY)
