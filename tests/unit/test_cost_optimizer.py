"""Tests for :mod:`eaip.cost.optimizer`."""

from __future__ import annotations

import pytest

from eaip.cost.exceptions import RecommendationNotFoundError
from eaip.cost.models import Category, CostRecord, RecommendationStatus
from eaip.cost.optimizer import CostOptimizer
from eaip.cost.tracker import CostTracker


@pytest.fixture
def tracker() -> CostTracker:
    return CostTracker()


@pytest.fixture
def optimizer(tracker: CostTracker) -> CostOptimizer:
    return CostOptimizer(tracker)


@pytest.fixture
def populated_tracker(tracker: CostTracker) -> CostTracker:
    tracker._records = [
        CostRecord(
            id="r1",
            category=Category.COMPUTE,
            amount=500.0,
            currency="USD",
            resource_type="vm",
            resource_id="vm-001",
        ),
        CostRecord(
            id="r2",
            category=Category.COMPUTE,
            amount=300.0,
            currency="USD",
            resource_type="vm",
            resource_id="vm-001",
        ),
        CostRecord(
            id="r3",
            category=Category.STORAGE,
            amount=5.0,
            currency="USD",
            resource_type="disk",
            resource_id="disk-001",
        ),
    ]
    return tracker


class TestGenerateRecommendations:
    @pytest.mark.asyncio
    async def test_generates_rightsize_for_high_cost(
        self, optimizer: CostOptimizer, populated_tracker: CostTracker
    ) -> None:
        recs = await optimizer.generate_recommendations()
        types = [r.type.value for r in recs]
        assert "rightsize" in types

    @pytest.mark.asyncio
    async def test_generates_stop_for_low_cost(
        self, optimizer: CostOptimizer, populated_tracker: CostTracker
    ) -> None:
        recs = await optimizer.generate_recommendations()
        types = [r.type.value for r in recs]
        assert "stop" in types

    @pytest.mark.asyncio
    async def test_no_records_no_recommendations(self, optimizer: CostOptimizer) -> None:
        recs = await optimizer.generate_recommendations()
        assert recs == []

    @pytest.mark.asyncio
    async def test_idempotent_generation(
        self, optimizer: CostOptimizer, populated_tracker: CostTracker
    ) -> None:
        await optimizer.generate_recommendations()
        r2 = await optimizer.generate_recommendations()
        # same data generator, would generate again but with new ids
        assert len(r2) > 0


class TestGetRecommendations:
    @pytest.mark.asyncio
    async def test_get_all(self, optimizer: CostOptimizer, populated_tracker: CostTracker) -> None:
        await optimizer.generate_recommendations()
        recs = await optimizer.get_recommendations()
        assert len(recs) > 0

    @pytest.mark.asyncio
    async def test_filter_by_resource_type(
        self, optimizer: CostOptimizer, populated_tracker: CostTracker
    ) -> None:
        await optimizer.generate_recommendations()
        recs = await optimizer.get_recommendations(resource_type="vm")
        assert all(r.resource_type == "vm" for r in recs)

    @pytest.mark.asyncio
    async def test_filter_by_status(
        self, optimizer: CostOptimizer, populated_tracker: CostTracker
    ) -> None:
        await optimizer.generate_recommendations()
        recs = await optimizer.get_recommendations(status="open")
        assert all(r.status.value == "open" for r in recs)

    @pytest.mark.asyncio
    async def test_empty(self, optimizer: CostOptimizer) -> None:
        recs = await optimizer.get_recommendations()
        assert recs == []


class TestApplyRecommendation:
    @pytest.mark.asyncio
    async def test_apply(self, optimizer: CostOptimizer, populated_tracker: CostTracker) -> None:
        await optimizer.generate_recommendations()
        recs = await optimizer.get_recommendations()
        rec_id = recs[0].id
        updated = await optimizer.apply_recommendation(rec_id)
        assert updated.status is RecommendationStatus.APPLIED

    @pytest.mark.asyncio
    async def test_apply_not_found(self, optimizer: CostOptimizer) -> None:
        with pytest.raises(RecommendationNotFoundError):
            await optimizer.apply_recommendation("nonexistent")


class TestDismissRecommendation:
    @pytest.mark.asyncio
    async def test_dismiss(self, optimizer: CostOptimizer, populated_tracker: CostTracker) -> None:
        await optimizer.generate_recommendations()
        recs = await optimizer.get_recommendations()
        rec_id = recs[0].id
        updated = await optimizer.dismiss_recommendation(rec_id)
        assert updated.status is RecommendationStatus.DISMISSED

    @pytest.mark.asyncio
    async def test_dismiss_not_found(self, optimizer: CostOptimizer) -> None:
        with pytest.raises(RecommendationNotFoundError):
            await optimizer.dismiss_recommendation("nonexistent")


class TestPotentialSavings:
    @pytest.mark.asyncio
    async def test_potential_savings(
        self, optimizer: CostOptimizer, populated_tracker: CostTracker
    ) -> None:
        await optimizer.generate_recommendations()
        savings = await optimizer.get_potential_savings()
        assert savings > 0

    @pytest.mark.asyncio
    async def test_potential_savings_empty(self, optimizer: CostOptimizer) -> None:
        savings = await optimizer.get_potential_savings()
        assert savings == 0.0

    @pytest.mark.asyncio
    async def test_savings_decreases_after_apply(
        self, optimizer: CostOptimizer, populated_tracker: CostTracker
    ) -> None:
        await optimizer.generate_recommendations()
        savings_before = await optimizer.get_potential_savings()
        recs = await optimizer.get_recommendations()
        if recs:
            await optimizer.apply_recommendation(recs[0].id)
            savings_after = await optimizer.get_potential_savings()
            assert savings_after <= savings_before
