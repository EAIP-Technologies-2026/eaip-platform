"""Tests for :mod:`eaip.resquota.events`."""

from __future__ import annotations

import pytest

from eaip.resquota.events import QuotaAllocated, QuotaExceeded, QuotaReleased, QuotaWarning


class TestQuotaExceeded:
    """Tests for :class:`eaip.resquota.events.QuotaExceeded`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = QuotaExceeded(quota_id="q1", consumer_id="c1", requested=150, limit=100)
        assert e.event_type == "eaip.resquota.quota.exceeded"
        assert e.requested == 150

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        e = QuotaExceeded(quota_id="q1", consumer_id="c1", requested=1, limit=1)
        with pytest.raises(ValueError):
            e.requested = 2


class TestQuotaAllocated:
    """Tests for :class:`eaip.resquota.events.QuotaAllocated`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = QuotaAllocated(quota_id="q1", consumer_id="c1", amount=50)
        assert e.event_type == "eaip.resquota.quota.allocated"


class TestQuotaReleased:
    """Tests for :class:`eaip.resquota.events.QuotaReleased`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = QuotaReleased(quota_id="q1", consumer_id="c1", amount=30)
        assert e.event_type == "eaip.resquota.quota.released"


class TestQuotaWarning:
    """Tests for :class:`eaip.resquota.events.QuotaWarning`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = QuotaWarning(quota_id="q1", consumer_id="c1", usage_percentage=85)
        assert e.event_type == "eaip.resquota.quota.warning"
        assert e.usage_percentage == 85


def test_all_events_have_unique_types() -> None:
    """Test that all event types are unique."""
    types = [
        QuotaExceeded(quota_id="q1", consumer_id="c1", requested=1, limit=1).event_type,
        QuotaAllocated(quota_id="q1", consumer_id="c1", amount=1).event_type,
        QuotaReleased(quota_id="q1", consumer_id="c1", amount=1).event_type,
        QuotaWarning(quota_id="q1", consumer_id="c1", usage_percentage=1).event_type,
    ]
    assert len(types) == len(set(types))
