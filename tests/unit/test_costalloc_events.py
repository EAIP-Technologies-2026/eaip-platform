"""Tests for :mod:`eaip.costalloc.events`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.costalloc.events import AllocationRuleCreated, AllocationRuleUpdated, CostAllocated


class TestCostAllocated:
    def test_minimal(self) -> None:
        now = datetime.now(UTC)
        e = CostAllocated(
            allocation_id="a1",
            tenant_id="t1",
            amount=500.0,
            currency="USD",
            period_start=now,
            period_end=now,
        )
        assert e.event_type == "eaip.costalloc.allocated"
        assert e.allocation_id == "a1"

    def test_frozen(self) -> None:
        now = datetime.now(UTC)
        e = CostAllocated(
            allocation_id="a1",
            tenant_id="t1",
            amount=100.0,
            currency="USD",
            period_start=now,
            period_end=now,
        )
        with pytest.raises(ValueError):
            e.amount = 200.0


class TestAllocationRuleCreated:
    def test_create(self) -> None:
        e = AllocationRuleCreated(
            rule_id="r1", name="Team A", dimension="department", percentage=50.0
        )
        assert e.event_type == "eaip.costalloc.rule.created"

    def test_with_criteria(self) -> None:
        e = AllocationRuleCreated(
            rule_id="r1",
            name="Team A",
            dimension="department",
            percentage=50.0,
            criteria={"dept": "eng"},
        )
        assert e.criteria["dept"] == "eng"


class TestAllocationRuleUpdated:
    def test_create(self) -> None:
        e = AllocationRuleUpdated(rule_id="r1", updates={"percentage": 75.0})
        assert e.event_type == "eaip.costalloc.rule.updated"
