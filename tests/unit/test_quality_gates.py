"""Tests for :mod:`eaip.quality.gates`."""

from __future__ import annotations

import pytest

from eaip.quality.exceptions import QualityGateError
from eaip.quality.gates import QualityGateService
from eaip.quality.models import (
    MetricOperator,
    QualityCondition,
    QualityGate,
    QualityGateStatus,
    TestExecution,
    TestExecutionStatus,
)

# Prevent pytest from collecting source classes as test classes
TestExecution.__test__ = False
TestExecutionStatus.__test__ = False


class TestGateRegistration:
    def test_register_and_get(self) -> None:
        svc = QualityGateService()
        g = QualityGate(id="g1", name="gate one")
        svc.register_gate(g)
        assert svc.get_gate("g1") is g

    def test_unregister_existing(self) -> None:
        svc = QualityGateService()
        svc.register_gate(QualityGate(id="g1", name="gate one"))
        svc.unregister_gate("g1")
        with pytest.raises(QualityGateError):
            svc.get_gate("g1")

    def test_unregister_missing(self) -> None:
        svc = QualityGateService()
        with pytest.raises(QualityGateError):
            svc.unregister_gate("nonexistent")

    def test_list_gates_empty(self) -> None:
        svc = QualityGateService()
        assert svc.list_gates() == []

    def test_list_gates(self) -> None:
        svc = QualityGateService()
        svc.register_gate(QualityGate(id="g1", name="a"))
        svc.register_gate(QualityGate(id="g2", name="b"))
        assert len(svc.list_gates()) == 2


class TestGateEvaluation:
    @pytest.mark.asyncio
    async def test_evaluate_no_conditions_passes(self) -> None:
        svc = QualityGateService()
        svc.register_gate(QualityGate(id="g1", name="gate one"))
        result = await svc.evaluate_gate("g1", [])
        assert result.status is QualityGateStatus.PASS

    @pytest.mark.asyncio
    async def test_evaluate_pass_rate_above(self) -> None:
        svc = QualityGateService()
        c = QualityCondition(metric="pass_rate", operator=MetricOperator.GTE, value=0.8)
        svc.register_gate(QualityGate(id="g1", name="gate one", conditions=(c,)))
        results = [
            TestExecution(id="e1", test_id="tc1", status=TestExecutionStatus.PASSED),
            TestExecution(id="e2", test_id="tc2", status=TestExecutionStatus.PASSED),
            TestExecution(id="e3", test_id="tc3", status=TestExecutionStatus.PASSED),
            TestExecution(id="e4", test_id="tc4", status=TestExecutionStatus.PASSED),
            TestExecution(id="e5", test_id="tc5", status=TestExecutionStatus.FAILED),
        ]
        result = await svc.evaluate_gate("g1", results)
        assert result.status is QualityGateStatus.PASS

    @pytest.mark.asyncio
    async def test_evaluate_pass_rate_below(self) -> None:
        svc = QualityGateService()
        c = QualityCondition(metric="pass_rate", operator=MetricOperator.GTE, value=0.9)
        svc.register_gate(QualityGate(id="g1", name="gate one", conditions=(c,)))
        results = [
            TestExecution(id="e1", test_id="tc1", status=TestExecutionStatus.PASSED),
            TestExecution(id="e2", test_id="tc2", status=TestExecutionStatus.FAILED),
            TestExecution(id="e3", test_id="tc3", status=TestExecutionStatus.FAILED),
        ]
        result = await svc.evaluate_gate("g1", results)
        assert result.status is QualityGateStatus.FAIL

    @pytest.mark.asyncio
    async def test_evaluate_failure_count(self) -> None:
        svc = QualityGateService()
        c = QualityCondition(metric="failure_count", operator=MetricOperator.LTE, value=0)
        svc.register_gate(QualityGate(id="g1", name="no failures", conditions=(c,)))
        results = [
            TestExecution(id="e1", test_id="tc1", status=TestExecutionStatus.PASSED),
            TestExecution(id="e2", test_id="tc2", status=TestExecutionStatus.FAILED),
        ]
        result = await svc.evaluate_gate("g1", results)
        assert result.status is QualityGateStatus.FAIL

    @pytest.mark.asyncio
    async def test_evaluate_avg_duration(self) -> None:
        svc = QualityGateService()
        c = QualityCondition(metric="avg_duration_ms", operator=MetricOperator.LT, value=500.0)
        svc.register_gate(QualityGate(id="g1", name="fast enough", conditions=(c,)))
        results = [
            TestExecution(
                id="e1", test_id="tc1", status=TestExecutionStatus.PASSED, duration_ms=100.0
            ),
            TestExecution(
                id="e2", test_id="tc2", status=TestExecutionStatus.PASSED, duration_ms=200.0
            ),
        ]
        result = await svc.evaluate_gate("g1", results)
        assert result.status is QualityGateStatus.PASS

    @pytest.mark.asyncio
    async def test_evaluate_empty_results_pass_rate(self) -> None:
        svc = QualityGateService()
        c = QualityCondition(metric="pass_rate", operator=MetricOperator.GTE, value=0.9)
        svc.register_gate(QualityGate(id="g1", name="gate one", conditions=(c,)))
        result = await svc.evaluate_gate("g1", [])
        assert result.status is QualityGateStatus.PASS

    @pytest.mark.asyncio
    async def test_evaluate_error_count(self) -> None:
        svc = QualityGateService()
        c = QualityCondition(metric="error_count", operator=MetricOperator.EQ, value=0)
        svc.register_gate(QualityGate(id="g1", name="no errors", conditions=(c,)))
        results = [
            TestExecution(id="e1", test_id="tc1", status=TestExecutionStatus.ERROR),
        ]
        result = await svc.evaluate_gate("g1", results)
        assert result.status is QualityGateStatus.FAIL


class TestEvaluateAllGates:
    @pytest.mark.asyncio
    async def test_evaluate_all_gates(self) -> None:
        svc = QualityGateService()
        svc.register_gate(QualityGate(id="g1", name="gate one"))
        svc.register_gate(QualityGate(id="g2", name="gate two"))
        results = await svc.evaluate_all_gates([])
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_evaluate_all_empty(self) -> None:
        svc = QualityGateService()
        results = await svc.evaluate_all_gates([])
        assert results == []


class TestPRReadiness:
    @pytest.mark.asyncio
    async def test_pr_ready(self) -> None:
        svc = QualityGateService()
        results = [
            TestExecution(id="e1", test_id="tc1", status=TestExecutionStatus.PASSED),
            TestExecution(id="e2", test_id="tc2", status=TestExecutionStatus.PASSED),
        ]
        check = await svc.check_pr_readiness("comp1", results)
        assert check["ready"] is True

    @pytest.mark.asyncio
    async def test_pr_not_ready_high_failures(self) -> None:
        svc = QualityGateService()
        results = [
            TestExecution(id="e1", test_id="tc1", status=TestExecutionStatus.FAILED),
            TestExecution(id="e2", test_id="tc2", status=TestExecutionStatus.FAILED),
        ]
        check = await svc.check_pr_readiness("comp1", results)
        assert check["ready"] is False

    @pytest.mark.asyncio
    async def test_pr_not_ready_errors(self) -> None:
        svc = QualityGateService()
        results = [
            TestExecution(id="e1", test_id="tc1", status=TestExecutionStatus.ERROR),
        ]
        check = await svc.check_pr_readiness("comp1", results)
        assert check["ready"] is False

    @pytest.mark.asyncio
    async def test_pr_readiness_empty_results(self) -> None:
        svc = QualityGateService()
        check = await svc.check_pr_readiness("comp1", [])
        assert check["ready"] is True
