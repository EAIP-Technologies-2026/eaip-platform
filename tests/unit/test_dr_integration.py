"""Tests for DR integration -- health check, runtime module, and full flow."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from eaip.dr.exceptions import (
    DrError,
    DrTestError,
    FailoverError,
    PlanNotFoundError,
    RtoViolationError,
    StepExecutionError,
)
from eaip.dr.failover import FailoverManager
from eaip.dr.health import DrHealthCheck
from eaip.dr.integration import DrRuntimeModule
from eaip.dr.models import DrPlan, DrStep, PlanStatus, StepStatus, StepType
from eaip.dr.plans import DrPlanManager
from eaip.dr.testing import DrTestService
from eaip.exceptions.base import EAIPError
from eaip.health.checks import HealthStatus


@pytest.fixture
def sample_plan() -> DrPlan:
    step = DrStep(
        id="s1",
        plan_id="plan_i",
        name="Verify",
        type=StepType.VERIFY,
        status=StepStatus.COMPLETED,
    )
    return DrPlan(
        id="plan_i",
        name="Integration Plan",
        status=PlanStatus.ACTIVE,
        steps=(step,),
    )


class TestDrHealthCheck:
    async def test_healthy_no_managers(self) -> None:
        hc = DrHealthCheck()
        report = await hc.check()
        assert report.component == "dr"
        assert report.status == HealthStatus.HEALTHY

    async def test_healthy_with_managers(self, sample_plan: DrPlan) -> None:
        pm = DrPlanManager()
        tested = sample_plan.model_copy(update={"last_tested_at": datetime.now(UTC)})
        pm.create_plan(tested)
        fm = FailoverManager()
        hc = DrHealthCheck(plan_manager=pm, failover_manager=fm)
        report = await hc.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.details["total_plans"] == 1

    async def test_degraded_untested_plans(self, sample_plan: DrPlan) -> None:
        pm = DrPlanManager()
        unested = sample_plan.model_copy(update={"last_tested_at": None})
        pm.create_plan(unested)
        hc = DrHealthCheck(plan_manager=pm)
        report = await hc.check()
        assert report.status == HealthStatus.DEGRADED
        assert "never been tested" in report.message


class TestDrRuntimeModule:
    @pytest.mark.asyncio  # type: ignore[misc]
    async def test_start_registers_capability_and_health(self) -> None:
        kernel = MagicMock()
        platform = MagicMock()
        capabilities = MagicMock()
        health = MagicMock()
        platform.capabilities = capabilities
        platform.health = health
        kernel.platform = platform

        module = DrRuntimeModule()
        await module.start(kernel)

        capabilities.register.assert_called_once()
        health.register.assert_called_once()
        registered_cap = capabilities.register.call_args[0][0]
        assert registered_cap.name == "eaip.dr"

    @pytest.mark.asyncio  # type: ignore[misc]
    async def test_stop_logs(self) -> None:
        kernel = MagicMock()
        module = DrRuntimeModule()
        await module.stop(kernel)

    def test_plan_manager_accessible(self) -> None:
        module = DrRuntimeModule()
        assert isinstance(module.plan_manager, DrPlanManager)

    def test_failover_manager_accessible(self) -> None:
        module = DrRuntimeModule()
        assert isinstance(module.failover_manager, FailoverManager)

    def test_test_service_accessible(self) -> None:
        module = DrRuntimeModule()
        assert isinstance(module.test_service, DrTestService)


class TestDrExceptions:
    def test_exception_hierarchy(self) -> None:
        assert issubclass(DrError, EAIPError)
        assert issubclass(PlanNotFoundError, DrError)
        assert issubclass(StepExecutionError, DrError)
        assert issubclass(FailoverError, DrError)
        assert issubclass(DrTestError, DrError)
        assert issubclass(RtoViolationError, DrError)

    def test_plan_not_found_message(self) -> None:
        err = PlanNotFoundError("test message", context={"plan_id": "p1"})
        assert "test message" in str(err)
        assert err.context["plan_id"] == "p1"
