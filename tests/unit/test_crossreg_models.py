"""Tests for :mod:`eaip.crossreg.models`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.crossreg.models import ReplicationConfig, ReplicationRule, ReplicationStatus


class TestReplicationRule:
    def test_create_minimal(self) -> None:
        r = ReplicationRule(
            id="r1",
            name="US-EU Sync",
            source_region="us-east",
            target_region="eu-west",
            resource_type="blob",
        )
        assert r.id == "r1"
        assert r.source_region == "us-east"
        assert r.target_region == "eu-west"
        assert r.sync_interval_seconds == 300
        assert r.enabled is True

    def test_custom_interval(self) -> None:
        r = ReplicationRule(
            id="r2",
            name="Fast Sync",
            source_region="us-east",
            target_region="eu-west",
            resource_type="table",
            sync_interval_seconds=60,
        )
        assert r.sync_interval_seconds == 60

    def test_disabled(self) -> None:
        r = ReplicationRule(
            id="r3",
            name="Off",
            source_region="us-east",
            target_region="eu-west",
            resource_type="blob",
            enabled=False,
        )
        assert r.enabled is False

    def test_frozen(self) -> None:
        r = ReplicationRule(
            id="r4", name="Test", source_region="us", target_region="eu", resource_type="blob"
        )
        with pytest.raises(ValidationError):
            r.enabled = False


class TestReplicationStatus:
    def test_defaults(self) -> None:
        s = ReplicationStatus(rule_id="r1")
        assert s.items_synced == 0
        assert s.items_failed == 0
        assert s.status == "idle"
        assert s.last_sync_at is None

    def test_with_values(self) -> None:
        now = datetime.now(UTC)
        s = ReplicationStatus(
            rule_id="r1", last_sync_at=now, items_synced=100, items_failed=2, status="running"
        )
        assert s.items_synced == 100
        assert s.items_failed == 2

    def test_frozen(self) -> None:
        s = ReplicationStatus(rule_id="r1")
        with pytest.raises(ValidationError):
            s.status = "running"


class TestReplicationConfig:
    def test_defaults(self) -> None:
        c = ReplicationConfig()
        assert c.max_retries == 3
        assert c.retry_delay_seconds == 30
        assert c.batch_size == 100
        assert c.enable_metrics is True

    def test_custom(self) -> None:
        c = ReplicationConfig(max_retries=5, batch_size=50, enable_metrics=False)
        assert c.max_retries == 5
        assert c.enable_metrics is False

    def test_frozen(self) -> None:
        c = ReplicationConfig()
        with pytest.raises(ValidationError):
            c.max_retries = 10


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        ReplicationRule(
            id="x",
            name="t",
            source_region="us",
            target_region="eu",
            resource_type="b",
            unknown="field",
        )
