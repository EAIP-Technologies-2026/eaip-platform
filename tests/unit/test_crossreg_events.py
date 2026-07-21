"""Tests for :mod:`eaip.crossreg.events`."""

from __future__ import annotations

import pytest

from eaip.crossreg.events import ReplicationCompleted, ReplicationFailed, ReplicationStarted


class TestReplicationStarted:
    def test_create(self) -> None:
        e = ReplicationStarted(
            rule_id="r1", name="US-EU Sync", source_region="us-east", target_region="eu-west"
        )
        assert e.event_type == "eaip.crossreg.replication.started"
        assert e.rule_id == "r1"

    def test_frozen(self) -> None:
        e = ReplicationStarted(rule_id="r1", name="Sync", source_region="us", target_region="eu")
        with pytest.raises(ValueError):
            e.name = "Changed"


class TestReplicationCompleted:
    def test_create(self) -> None:
        e = ReplicationCompleted(
            rule_id="r1", items_synced=100, items_failed=0, duration_seconds=12.5
        )
        assert e.event_type == "eaip.crossreg.replication.completed"

    def test_default_duration(self) -> None:
        e = ReplicationCompleted(rule_id="r1", items_synced=50, items_failed=1)
        assert e.duration_seconds is None


class TestReplicationFailed:
    def test_create(self) -> None:
        e = ReplicationFailed(rule_id="r1", error="Connection timeout")
        assert e.event_type == "eaip.crossreg.replication.failed"
        assert e.error == "Connection timeout"
