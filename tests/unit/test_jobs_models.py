"""Tests for job models."""

from __future__ import annotations

import pytest

from eaip.jobs.models import (
    CronExpression,
    JobDefinition,
    JobPriority,
    JobRun,
    JobSchedule,
    JobStatus,
    RetryConfig,
)


class TestCronExpression:
    def test_defaults(self) -> None:
        c = CronExpression()
        assert c.minute == "*"
        assert c.to_cron_string() == "* * * * *"

    def test_custom(self) -> None:
        c = CronExpression(minute="0", hour="9", day_of_week="1-5")
        assert c.to_cron_string() == "0 9 * * 1-5"

    def test_from_string(self) -> None:
        c = CronExpression.from_string("0 9 * * 1-5")
        assert c.minute == "0"
        assert c.hour == "9"
        assert c.day_of_week == "1-5"

    def test_from_string_invalid(self) -> None:
        with pytest.raises(ValueError):
            CronExpression.from_string("invalid")


class TestRetryConfig:
    def test_defaults(self) -> None:
        r = RetryConfig()
        assert r.max_retries == 3
        assert r.delay_seconds == 5.0


class TestJobSchedule:
    def test_defaults(self) -> None:
        s = JobSchedule()
        assert s.cron is None
        assert s.interval_seconds is None


class TestJobDefinition:
    def test_defaults(self) -> None:
        d = JobDefinition(id="job_1", name="Test Job")
        assert d.priority is JobPriority.NORMAL
        assert d.enabled is True

    def test_with_schedule(self) -> None:
        d = JobDefinition(
            id="job_2",
            name="Scheduled Job",
            schedule=JobSchedule(interval_seconds=300.0),
            priority=JobPriority.HIGH,
            timeout_seconds=60.0,
            tags=("production",),
        )
        assert d.schedule is not None
        assert d.schedule.interval_seconds == 300.0
        assert d.priority is JobPriority.HIGH


class TestJobRun:
    def test_defaults(self) -> None:
        r = JobRun(id="run_1", job_id="job_1")
        assert r.status is JobStatus.PENDING
        assert r.progress == 0.0
        assert r.attempt == 0

    def test_completed(self) -> None:
        r = JobRun(
            id="run_1",
            job_id="job_1",
            status=JobStatus.COMPLETED,
            result="success",
            duration_ms=1500.0,
        )
        assert r.result == "success"
        assert r.duration_ms == 1500.0
