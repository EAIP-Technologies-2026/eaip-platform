"""Quality gates — evaluate conditions against test results."""

from __future__ import annotations

from typing import Any

from eaip.quality.exceptions import QualityGateError
from eaip.quality.models import (
    MetricOperator,
    QualityCondition,
    QualityGate,
    QualityGateStatus,
    TestExecution,
    TestExecutionStatus,
)
from eaip.shared.time import utc_now


def _evaluate_condition(condition: QualityCondition, actual_value: float) -> bool:
    if condition.operator is MetricOperator.GT:
        return actual_value > condition.value
    if condition.operator is MetricOperator.GTE:
        return actual_value >= condition.value
    if condition.operator is MetricOperator.LT:
        return actual_value < condition.value
    if condition.operator is MetricOperator.LTE:
        return actual_value <= condition.value
    if condition.operator is MetricOperator.EQ:
        return actual_value == condition.value
    # MetricOperator.NEQ is the final case
    return actual_value != condition.value


def _extract_metric(metric: str, test_results: list[TestExecution]) -> float:
    if metric == "pass_rate":
        if not test_results:
            return 1.0
        passed = sum(1 for r in test_results if r.status is TestExecutionStatus.PASSED)
        return passed / len(test_results)
    if metric == "failure_count":
        return sum(1 for r in test_results if r.status is TestExecutionStatus.FAILED)
    if metric == "error_count":
        return float(sum(1 for r in test_results if r.status is TestExecutionStatus.ERROR))
    if metric == "total_count":
        return float(len(test_results))
    if metric == "avg_duration_ms":
        if not test_results:
            return 0.0
        durations = [r.duration_ms for r in test_results if r.duration_ms > 0]
        if not durations:
            return 0.0
        return sum(durations) / len(durations)
    if metric == "skip_count":
        return float(sum(1 for r in test_results if r.status is TestExecutionStatus.SKIPPED))
    return 0.0


class QualityGateService:
    def __init__(self) -> None:
        self._gates: dict[str, QualityGate] = {}

    def register_gate(self, gate: QualityGate) -> None:
        self._gates[gate.id] = gate

    def unregister_gate(self, gate_id: str) -> None:
        if gate_id not in self._gates:
            raise QualityGateError(f"Gate {gate_id!r} not found")
        del self._gates[gate_id]

    def get_gate(self, gate_id: str) -> QualityGate:
        if gate_id not in self._gates:
            raise QualityGateError(f"Gate {gate_id!r} not found")
        return self._gates[gate_id]

    def list_gates(self) -> list[QualityGate]:
        return list(self._gates.values())

    async def evaluate_gate(
        self,
        gate_id: str,
        test_results: list[TestExecution],
    ) -> QualityGate:
        gate = self.get_gate(gate_id)
        if not gate.conditions:
            evaluated = QualityGate(
                id=gate.id,
                name=gate.name,
                description=gate.description,
                conditions=gate.conditions,
                status=QualityGateStatus.PASS,
                evaluated_at=utc_now(),
                metadata=gate.metadata,
            )
            self._gates[gate_id] = evaluated
            return evaluated

        all_passed = True
        for condition in gate.conditions:
            actual = _extract_metric(condition.metric, test_results)
            if not _evaluate_condition(condition, actual):
                all_passed = False
                break

        evaluated = QualityGate(
            id=gate.id,
            name=gate.name,
            description=gate.description,
            conditions=gate.conditions,
            status=QualityGateStatus.PASS if all_passed else QualityGateStatus.FAIL,
            evaluated_at=utc_now(),
            metadata=gate.metadata,
        )
        self._gates[gate_id] = evaluated
        return evaluated

    async def evaluate_all_gates(
        self,
        test_results: list[TestExecution],
    ) -> list[QualityGate]:
        results: list[QualityGate] = []
        for gate_id in list(self._gates.keys()):
            result = await self.evaluate_gate(gate_id, test_results)
            results.append(result)
        return results

    async def check_pr_readiness(
        self,
        component: str,
        test_results: list[TestExecution],
    ) -> dict[str, Any]:
        if not test_results:
            return {"ready": True, "reason": "No tests executed"}

        pass_rate = _extract_metric("pass_rate", test_results)
        failure_count = int(_extract_metric("failure_count", test_results))
        error_count = int(_extract_metric("error_count", test_results))

        ready = pass_rate >= 0.9 and failure_count == 0 and error_count == 0
        reasons: list[str] = []
        if pass_rate < 0.9:
            reasons.append(f"Pass rate {pass_rate:.1%} below 90%")
        if failure_count > 0:
            reasons.append(f"{failure_count} failure(s)")
        if error_count > 0:
            reasons.append(f"{error_count} error(s)")

        return {
            "ready": ready,
            "pass_rate": pass_rate,
            "failure_count": failure_count,
            "error_count": error_count,
            "total": len(test_results),
            "reason": "; ".join(reasons) if reasons else "All checks passed",
        }
