"""DR testing — run, schedule, compare tests and generate reports."""

from __future__ import annotations

import time
import uuid
from typing import Any

from eaip.dr.events import DrPlanTested, DrPlanTestFailed
from eaip.dr.exceptions import DrTestError, PlanNotFoundError
from eaip.dr.models import (
    DrPlan,
    DrTestResult,
    DrTestResultStatus,
    PlanStatus,
    StepStatus,
)
from eaip.logging.context import get_logger


class DrTestService:
    """Service for running and managing DR plan tests."""

    def __init__(self, event_bus: Any = None) -> None:
        self._plans: dict[str, DrPlan] = {}
        self._results: dict[str, DrTestResult] = {}
        self._schedules: dict[str, float] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.dr.testing")

    def register_plan(self, plan: DrPlan) -> None:
        self._plans[plan.id] = plan

    async def run_test(self, plan_id: str) -> DrTestResult:  # noqa: PLR0912
        plan = self._plans.get(plan_id)
        if plan is None:
            raise PlanNotFoundError(
                f"DR plan {plan_id!r} not found",
                context={"plan_id": plan_id},
            )

        allowed = (PlanStatus.DRAFT, PlanStatus.ACTIVE, PlanStatus.TESTED, PlanStatus.FAILED)
        if plan.status not in allowed:
            raise DrTestError(
                f"Cannot test plan {plan_id} in status {plan.status}",
                context={"plan_id": plan_id, "status": str(plan.status)},
            )

        t0 = time.monotonic()
        steps_passed = 0
        steps_failed = 0
        findings: list[str] = []
        recommendations: list[str] = []

        for step in plan.steps:
            if step.status == StepStatus.FAILED:
                steps_failed += 1
                findings.append(f"Step {step.name!r} ({step.id}) failed: {step.error}")
            elif step.status == StepStatus.COMPLETED:
                steps_passed += 1
            else:
                steps_failed += 1
                findings.append(f"Step {step.name!r} ({step.id}) was not executed")

        total_steps = len(plan.steps) or 1
        if steps_failed == 0:
            status = DrTestResultStatus.PASSED
        elif steps_passed > 0:
            status = DrTestResultStatus.PARTIAL
        else:
            status = DrTestResultStatus.FAILED

        if status == DrTestResultStatus.PASSED:
            recommendations.append("Review plan for ongoing relevance")
        elif status == DrTestResultStatus.PARTIAL:
            recommendations.append("Investigate and fix failed steps before next test")
        else:
            recommendations.append("All steps failed — review plan configuration and dependencies")

        rto_achieved = time.monotonic() - t0
        if rto_achieved > plan.rto_seconds:
            findings.append(f"RTO exceeded: {rto_achieved:.1f}s vs {plan.rto_seconds}s target")

        result = DrTestResult(
            id=str(uuid.uuid4()),
            plan_id=plan_id,
            status=status,
            completed_at=None,
            duration_ms=rto_achieved * 1000,
            rto_achieved_seconds=rto_achieved,
            rpo_achieved_seconds=0.0,
            steps_passed=steps_passed,
            steps_failed=steps_failed,
            steps_total=total_steps,
            findings=tuple(findings),
            recommendations=tuple(recommendations),
        )
        self._results[result.id] = result

        new_plan_status = (
            PlanStatus.TESTED if status == DrTestResultStatus.PASSED else PlanStatus.FAILED
        )
        updated_plan = plan.model_copy(
            update={
                "status": new_plan_status,
                "last_tested_at": None,
                "test_results": (*plan.test_results, result),
            },
        )
        self._plans[plan_id] = updated_plan

        if self._event_bus is not None:
            if status == DrTestResultStatus.PASSED:
                self._event_bus.publish(DrPlanTested(plan_id=plan_id, result=result))
            else:
                self._event_bus.publish(
                    DrPlanTestFailed(
                        plan_id=plan_id,
                        error=f"Test {status.value}: {'; '.join(findings)}",
                    )
                )

        self._log.info(
            "dr.test.completed",
            plan_id=plan_id,
            status=str(status),
            duration_ms=result.duration_ms,
        )
        return result

    async def schedule_test(self, plan_id: str, interval_days: int) -> None:
        if plan_id not in self._plans:
            raise PlanNotFoundError(
                f"DR plan {plan_id!r} not found",
                context={"plan_id": plan_id},
            )
        self._schedules[plan_id] = interval_days * 86400.0
        self._log.info("dr.test.scheduled", plan_id=plan_id, interval_days=interval_days)

    async def get_test_history(self, plan_id: str, limit: int = 10) -> list[DrTestResult]:
        results = [r for r in self._results.values() if r.plan_id == plan_id]
        results.sort(key=lambda r: r.started_at, reverse=True)
        return results[:limit]

    async def compare_tests(
        self,
        plan_id: str,
        test_a_id: str,
        test_b_id: str,
    ) -> dict[str, Any]:
        test_a = self._results.get(test_a_id)
        test_b = self._results.get(test_b_id)

        if test_a is None or test_b is None:
            raise DrTestError(
                "One or both test results not found",
                context={
                    "plan_id": plan_id,
                    "test_a": test_a_id,
                    "test_b": test_b_id,
                },
            )

        return {
            "plan_id": plan_id,
            "test_a": {
                "id": test_a.id,
                "status": str(test_a.status),
                "duration_ms": test_a.duration_ms,
                "rto_achieved_seconds": test_a.rto_achieved_seconds,
                "steps_passed": test_a.steps_passed,
                "steps_failed": test_a.steps_failed,
                "findings": list(test_a.findings),
            },
            "test_b": {
                "id": test_b.id,
                "status": str(test_b.status),
                "duration_ms": test_b.duration_ms,
                "rto_achieved_seconds": test_b.rto_achieved_seconds,
                "steps_passed": test_b.steps_passed,
                "steps_failed": test_b.steps_failed,
                "findings": list(test_b.findings),
            },
            "differences": {
                "duration_change_ms": test_b.duration_ms - test_a.duration_ms,
                "rto_change_seconds": (
                    (test_b.rto_achieved_seconds or 0) - (test_a.rto_achieved_seconds or 0)
                ),
                "steps_passed_change": test_b.steps_passed - test_a.steps_passed,
                "steps_failed_change": test_b.steps_failed - test_a.steps_failed,
            },
        }

    async def generate_test_report(self, plan_id: str) -> dict[str, Any]:
        plan = self._plans.get(plan_id)
        if plan is None:
            raise PlanNotFoundError(
                f"DR plan {plan_id!r} not found",
                context={"plan_id": plan_id},
            )

        history = await self.get_test_history(plan_id, limit=20)
        passed = sum(1 for r in history if r.status == DrTestResultStatus.PASSED)
        failed = sum(1 for r in history if r.status == DrTestResultStatus.FAILED)
        partial = sum(1 for r in history if r.status == DrTestResultStatus.PARTIAL)

        avg_duration = 0.0
        avg_rto = 0.0
        if history:
            avg_duration = sum(r.duration_ms for r in history) / len(history)
            avg_rto = sum((r.rto_achieved_seconds or 0) for r in history) / len(history)

        return {
            "plan_id": plan_id,
            "plan_name": plan.name,
            "plan_status": str(plan.status),
            "total_tests": len(history),
            "passed": passed,
            "failed": failed,
            "partial": partial,
            "pass_rate": round(passed / len(history) * 100, 1) if history else 0.0,
            "avg_duration_ms": round(avg_duration, 2),
            "avg_rto_achieved_seconds": round(avg_rto, 2),
            "rto_target_seconds": plan.rto_seconds,
            "rpo_target_seconds": plan.rpo_seconds,
            "scheduled_interval_days": self._schedules.get(plan_id),
        }


__all__ = ["DrTestService"]
