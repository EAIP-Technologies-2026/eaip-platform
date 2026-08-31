"""Tests for DR test service."""

from __future__ import annotations

import pytest

from eaip.dr.exceptions import DrTestError, PlanNotFoundError
from eaip.dr.models import (
    DrPlan,
    DrStep,
    DrTestResultStatus,
    PlanStatus,
    StepStatus,
    StepType,
)
from eaip.dr.testing import DrTestService


@pytest.fixture
def sample_plan() -> DrPlan:
    step1 = DrStep(
        id="s1",
        plan_id="plan_t",
        name="Verify",
        type=StepType.VERIFY,
        status=StepStatus.COMPLETED,
    )
    step2 = DrStep(
        id="s2",
        plan_id="plan_t",
        name="Failover",
        type=StepType.FAILOVER,
        status=StepStatus.COMPLETED,
    )
    return DrPlan(
        id="plan_t",
        name="Test Plan",
        status=PlanStatus.ACTIVE,
        steps=(step1, step2),
    )


@pytest.fixture
def service(sample_plan: DrPlan) -> DrTestService:
    s = DrTestService()
    s.register_plan(sample_plan)
    return s


class TestDrTestService:
    async def test_run_test_passed(self, service: DrTestService) -> None:
        result = await service.run_test("plan_t")
        assert result.status == DrTestResultStatus.PASSED
        assert result.duration_ms > 0
        assert result.plan_id == "plan_t"

    async def test_run_test_plan_not_found(self, service: DrTestService) -> None:
        with pytest.raises(PlanNotFoundError):
            await service.run_test("nonexistent")

    async def test_run_test_tracks_failures(
        self,
        service: DrTestService,
        sample_plan: DrPlan,
    ) -> None:
        failed_steps = (
            DrStep(
                id="s1",
                plan_id="plan_t",
                name="Failed Step",
                type=StepType.VERIFY,
                status=StepStatus.FAILED,
                error="Connection timeout",
            ),
            DrStep(
                id="s2",
                plan_id="plan_t",
                name="Good Step",
                type=StepType.FAILOVER,
                status=StepStatus.COMPLETED,
            ),
        )
        plan = sample_plan.model_copy(update={"steps": failed_steps})
        service.register_plan(plan)
        result = await service.run_test("plan_t")
        assert result.status == DrTestResultStatus.PARTIAL
        assert result.steps_failed == 1
        assert result.steps_passed == 1

    async def test_run_test_all_failed(
        self,
        service: DrTestService,
        sample_plan: DrPlan,
    ) -> None:
        failed_steps = (
            DrStep(
                id="s1",
                plan_id="plan_t",
                name="Step 1",
                type=StepType.VERIFY,
                status=StepStatus.FAILED,
            ),
            DrStep(
                id="s2",
                plan_id="plan_t",
                name="Step 2",
                type=StepType.FAILOVER,
                status=StepStatus.FAILED,
            ),
        )
        plan = sample_plan.model_copy(update={"steps": failed_steps})
        service.register_plan(plan)
        result = await service.run_test("plan_t")
        assert result.status == DrTestResultStatus.FAILED

    async def test_run_test_skipped_as_failure(
        self,
        service: DrTestService,
        sample_plan: DrPlan,
    ) -> None:
        mixed_steps = (
            DrStep(
                id="s1",
                plan_id="plan_t",
                name="Done",
                type=StepType.VERIFY,
                status=StepStatus.COMPLETED,
            ),
            DrStep(
                id="s2",
                plan_id="plan_t",
                name="Pending",
                type=StepType.FAILOVER,
                status=StepStatus.PENDING,
            ),
        )
        plan = sample_plan.model_copy(update={"steps": mixed_steps})
        service.register_plan(plan)
        result = await service.run_test("plan_t")
        assert result.steps_failed == 1
        assert "was not executed" in result.findings[0]

    async def test_schedule_test(self, service: DrTestService) -> None:
        await service.schedule_test("plan_t", interval_days=7)
        assert "plan_t" in service._schedules
        assert service._schedules["plan_t"] == 7 * 86400.0

    async def test_schedule_test_not_found(self, service: DrTestService) -> None:
        with pytest.raises(PlanNotFoundError):
            await service.schedule_test("nonexistent", 7)

    async def test_get_test_history(self, service: DrTestService) -> None:
        await service.run_test("plan_t")
        await service.run_test("plan_t")
        history = await service.get_test_history("plan_t")
        assert len(history) == 2

    async def test_get_test_history_empty(self, service: DrTestService) -> None:
        history = await service.get_test_history("plan_t")
        assert history == []

    async def test_compare_tests(self, service: DrTestService) -> None:
        result_a = await service.run_test("plan_t")
        result_b = await service.run_test("plan_t")
        comparison = await service.compare_tests("plan_t", result_a.id, result_b.id)
        assert comparison["plan_id"] == "plan_t"
        assert "differences" in comparison
        assert "duration_change_ms" in comparison["differences"]

    async def test_compare_tests_not_found(self, service: DrTestService) -> None:
        result = await service.run_test("plan_t")
        with pytest.raises(DrTestError):
            await service.compare_tests("plan_t", result.id, "nonexistent")

    async def test_generate_test_report(self, service: DrTestService) -> None:
        await service.run_test("plan_t")
        report = await service.generate_test_report("plan_t")
        assert report["plan_id"] == "plan_t"
        assert report["total_tests"] == 1
        assert report["pass_rate"] == 100.0

    async def test_generate_test_report_no_history(
        self,
        service: DrTestService,
    ) -> None:
        report = await service.generate_test_report("plan_t")
        assert report["total_tests"] == 0
        assert report["pass_rate"] == 0.0

    async def test_generate_test_report_not_found(
        self,
        service: DrTestService,
    ) -> None:
        with pytest.raises(PlanNotFoundError):
            await service.generate_test_report("nonexistent")
