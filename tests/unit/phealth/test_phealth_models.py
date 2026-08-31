"""Tests for :mod:`eaip.phealth.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.phealth.models import HealthAlert, HealthDashboard, HealthMetric, HealthSnapshot


class TestHealthSnapshot:
    """Tests for :class:`eaip.phealth.models.HealthSnapshot`."""

    def test_create_minimal(self) -> None:
        """Test creating a snapshot with required fields."""
        s = HealthSnapshot(id="s1", component="api", status="healthy")
        assert s.metrics == {}
        assert s.status == "healthy"

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        s = HealthSnapshot(id="s1", component="c", status="ok")
        with pytest.raises(ValidationError):
            s.status = "bad"


class TestHealthMetric:
    """Tests for :class:`eaip.phealth.models.HealthMetric`."""

    def test_create_minimal(self) -> None:
        """Test creating a metric with required fields."""
        m = HealthMetric(name="cpu", value=0.5)
        assert m.breached is False
        assert m.unit == ""

    def test_with_threshold(self) -> None:
        """Test creating a metric with a threshold."""
        m = HealthMetric(name="cpu", value=0.9, threshold=0.8, breached=True)
        assert m.breached is True
        assert m.threshold == 0.8

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        m = HealthMetric(name="cpu", value=0.5)
        with pytest.raises(ValidationError):
            m.value = 0.9


class TestHealthDashboard:
    """Tests for :class:`eaip.phealth.models.HealthDashboard`."""

    def test_create_minimal(self) -> None:
        """Test creating a dashboard with required fields."""
        d = HealthDashboard(id="d1", name="System Health")
        assert d.is_active is True
        assert d.components == ()

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        d = HealthDashboard(id="d1", name="n")
        with pytest.raises(ValidationError):
            d.name = "changed"


class TestHealthAlert:
    """Tests for :class:`eaip.phealth.models.HealthAlert`."""

    def test_create_minimal(self) -> None:
        """Test creating an alert with required fields."""
        a = HealthAlert(
            id="a1",
            metric_name="cpu",
            component="api",
            value=0.9,
            threshold=0.8,
        )
        assert a.resolved is False
        assert a.severity == "warning"

    def test_resolved(self) -> None:
        """Test creating a resolved alert."""
        a = HealthAlert(
            id="a1",
            metric_name="cpu",
            component="api",
            value=0.9,
            threshold=0.8,
            severity="critical",
            resolved=True,
        )
        assert a.resolved is True
        assert a.severity == "critical"

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        a = HealthAlert(id="a1", metric_name="m", component="c", value=1, threshold=1)
        with pytest.raises(ValidationError):
            a.severity = "info"


def test_extra_fields_forbidden() -> None:
    """Test that extra fields are rejected."""
    with pytest.raises(ValidationError):
        HealthSnapshot(id="s1", component="c", status="ok", unknown="val")
