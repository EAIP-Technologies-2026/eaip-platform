"""Tests for eventret domain events."""

from __future__ import annotations

import pytest

from eaip.eventret.events import (
    PolicyApplied,
    PolicyCreated,
    RetentionJobCompleted,
    RetentionJobFailed,
)
from eaip.eventret.models import RetentionAction
from eaip.events.event import DomainEvent


class TestPolicyCreated:
    def test_defaults(self) -> None:
        e = PolicyCreated(policy_id="p1", name="cleanup-90d", action=RetentionAction.DELETE)
        assert e.event_type == "eaip.eventret.policy.created"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = PolicyCreated(
            policy_id="p1", name="cleanup-90d", action=RetentionAction.ARCHIVE, enabled=False
        )
        assert e.action == RetentionAction.ARCHIVE
        assert e.enabled is False


class TestPolicyApplied:
    def test_defaults(self) -> None:
        e = PolicyApplied(policy_id="p1", name="cleanup-90d", action=RetentionAction.DELETE)
        assert e.event_type == "eaip.eventret.policy.applied"
        assert e.affected_events == 0

    def test_with_values(self) -> None:
        e = PolicyApplied(
            policy_id="p1", name="cleanup-90d", action=RetentionAction.COMPRESS, affected_events=500
        )
        assert e.affected_events == 500


class TestRetentionJobCompleted:
    def test_defaults(self) -> None:
        e = RetentionJobCompleted(job_id="j1", policy_id="p1")
        assert e.event_type == "eaip.eventret.job.completed"
        assert e.affected_events == 0

    def test_with_values(self) -> None:
        e = RetentionJobCompleted(
            job_id="j1", policy_id="p1", affected_events=200, duration_seconds=12.5
        )
        assert e.affected_events == 200
        assert e.duration_seconds == 12.5


class TestRetentionJobFailed:
    def test_defaults(self) -> None:
        e = RetentionJobFailed(job_id="j1", policy_id="p1")
        assert e.event_type == "eaip.eventret.job.failed"

    def test_with_error(self) -> None:
        e = RetentionJobFailed(job_id="j1", policy_id="p1", error_message="Connection timeout")
        assert e.error_message == "Connection timeout"

    def test_frozen(self) -> None:
        e = RetentionJobFailed(job_id="j1", policy_id="p1")
        with pytest.raises((ValueError, TypeError)):
            e.job_id = "j2"


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [PolicyCreated, PolicyApplied, RetentionJobCompleted, RetentionJobFailed]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
