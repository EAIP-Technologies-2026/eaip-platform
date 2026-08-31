"""Tests for :mod:`eaip.resquota.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.resquota.models import QuotaAllocation, QuotaConfig, QuotaUsage, ResourceQuota


class TestResourceQuota:
    """Tests for :class:`eaip.resquota.models.ResourceQuota`."""

    def test_create_minimal(self) -> None:
        """Test creating a quota with required fields."""
        q = ResourceQuota(id="q1", name="CPU Quota", limit=100, unit="cores")
        assert q.allocated == 0
        assert q.unit == "cores"

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        q = ResourceQuota(id="q1", name="CPU", limit=100, unit="cores")
        with pytest.raises(ValidationError):
            q.limit = 200


class TestQuotaAllocation:
    """Tests for :class:`eaip.resquota.models.QuotaAllocation`."""

    def test_create_minimal(self) -> None:
        """Test creating an allocation with required fields."""
        a = QuotaAllocation(quota_id="q1", amount=10, consumer_id="c1")
        assert a.amount == 10

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        a = QuotaAllocation(quota_id="q1", amount=10, consumer_id="c1")
        with pytest.raises(ValidationError):
            a.amount = 20


class TestQuotaConfig:
    """Tests for :class:`eaip.resquota.models.QuotaConfig`."""

    def test_defaults(self) -> None:
        """Test default configuration values."""
        c = QuotaConfig()
        assert c.default_limit == 1000
        assert c.warn_threshold == 0.8
        assert c.enforce_strict is True

    def test_custom(self) -> None:
        """Test creating a config with custom values."""
        c = QuotaConfig(default_limit=500, warn_threshold=0.9, enforce_strict=False)
        assert c.default_limit == 500
        assert c.warn_threshold == 0.9
        assert c.enforce_strict is False

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        c = QuotaConfig()
        with pytest.raises(ValidationError):
            c.default_limit = 999


class TestQuotaUsage:
    """Tests for :class:`eaip.resquota.models.QuotaUsage`."""

    def test_create(self) -> None:
        """Test creating a usage snapshot."""
        u = QuotaUsage(quota_id="q1", consumer_id="c1", used=50, limit=100, percentage=50)
        assert u.used == 50
        assert u.percentage == 50

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        u = QuotaUsage(quota_id="q1", consumer_id="c1", used=0, limit=100, percentage=0)
        with pytest.raises(ValidationError):
            u.used = 10


def test_extra_fields_forbidden() -> None:
    """Test that extra fields are rejected."""
    with pytest.raises(ValidationError):
        ResourceQuota(id="q1", name="Test", limit=10, unit="u", unknown="val")
