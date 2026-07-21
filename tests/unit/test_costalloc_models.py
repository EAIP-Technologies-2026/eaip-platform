"""Tests for :mod:`eaip.costalloc.models`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.costalloc.models import AllocationConfig, AllocationRule, CostAllocation


class TestCostAllocation:
    def test_create_minimal(self) -> None:
        now = datetime.now(UTC)
        a = CostAllocation(
            id="a1",
            tenant_id="t1",
            amount=500.0,
            currency="USD",
            period_start=now,
            period_end=now,
        )
        assert a.id == "a1"
        assert a.tenant_id == "t1"
        assert a.amount == 500.0
        assert a.department is None

    def test_create_full(self) -> None:
        now = datetime.now(UTC)
        a = CostAllocation(
            id="a2",
            tenant_id="t1",
            department="Engineering",
            project="ProjectX",
            cost_center="CC-001",
            amount=1000.0,
            currency="USD",
            period_start=now,
            period_end=now,
        )
        assert a.department == "Engineering"
        assert a.cost_center == "CC-001"

    def test_frozen(self) -> None:
        now = datetime.now(UTC)
        a = CostAllocation(
            id="a3", tenant_id="t1", amount=100.0, currency="USD", period_start=now, period_end=now
        )
        with pytest.raises(ValidationError):
            a.amount = 200.0


class TestAllocationRule:
    def test_create_minimal(self) -> None:
        r = AllocationRule(
            id="r1",
            name="Team A",
            dimension="department",
            criteria={"dept": "eng"},
            percentage=50.0,
        )
        assert r.name == "Team A"
        assert r.percentage == 50.0
        assert r.enabled is True

    def test_custom_percentage(self) -> None:
        r = AllocationRule(id="r2", name="Team B", dimension="project", percentage=25.0)
        assert r.percentage == 25.0

    def test_frozen(self) -> None:
        r = AllocationRule(id="r3", name="Team C", dimension="cost_center", percentage=10.0)
        with pytest.raises(ValidationError):
            r.percentage = 20.0


class TestAllocationConfig:
    def test_defaults(self) -> None:
        c = AllocationConfig()
        assert c.default_currency == "USD"
        assert c.auto_allocate is True
        assert c.allocation_interval_hours == 24
        assert c.data_retention_days == 365

    def test_custom(self) -> None:
        c = AllocationConfig(default_currency="EUR", auto_allocate=False, data_retention_days=90)
        assert c.default_currency == "EUR"
        assert c.auto_allocate is False

    def test_frozen(self) -> None:
        c = AllocationConfig()
        with pytest.raises(ValidationError):
            c.default_currency = "GBP"

    def test_with_rules(self) -> None:
        now = datetime.now(UTC)
        rules = (
            AllocationRule(id="r1", name="R1", dimension="dept", percentage=50.0),
            AllocationRule(id="r2", name="R2", dimension="project", percentage=50.0),
        )
        allocations = (
            CostAllocation(
                id="a1",
                tenant_id="t1",
                amount=100.0,
                currency="USD",
                period_start=now,
                period_end=now,
            ),
        )
        c = AllocationConfig(rules=rules)
        assert len(c.rules) == 2


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        CostAllocation(
            id="x",
            tenant_id="t1",
            amount=1.0,
            currency="USD",
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC),
            unknown="field",
        )
