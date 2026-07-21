"""Tests for :mod:`eaip.quality.events`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.quality.events import (
    CoverageReported,
    QualityGateEvaluated,
    QualityGateFailed,
    QualityGatePassed,
    RegressionCleared,
    RegressionDetected,
    SuiteRegistered,
    TestCaseRegistered,
    TestCaseUnregistered,
    TestExecutionCompleted,
    TestExecutionFailed,
    TestExecutionStarted,
)

# Prevent pytest from collecting source classes as test classes
TestCaseRegistered.__test__ = False
TestCaseUnregistered.__test__ = False
TestExecutionStarted.__test__ = False
TestExecutionCompleted.__test__ = False
TestExecutionFailed.__test__ = False


class TestTestCaseEvents:
    def test_registered(self) -> None:
        e = TestCaseRegistered(test_id="tc1", name="test one", type="unit", component="comp1")
        assert e.event_type == "eaip.quality.test_case.registered"
        assert e.test_id == "tc1"
        assert e.name == "test one"

    def test_unregistered(self) -> None:
        e = TestCaseUnregistered(test_id="tc1")
        assert e.event_type == "eaip.quality.test_case.unregistered"
        assert e.test_id == "tc1"

    def test_registered_immutable(self) -> None:
        e = TestCaseRegistered(test_id="tc1", name="test one", type="unit", component="comp1")
        with pytest.raises(ValidationError):
            e.test_id = "changed"

    def test_registered_has_occurred_at(self) -> None:
        e = TestCaseRegistered(test_id="tc1", name="test one", type="unit", component="comp1")
        assert e.occurred_at is not None


class TestTestExecutionEvents:
    def test_started(self) -> None:
        e = TestExecutionStarted(execution_id="e1", test_id="tc1")
        assert e.event_type == "eaip.quality.test_execution.started"
        assert e.execution_id == "e1"

    def test_completed(self) -> None:
        e = TestExecutionCompleted(
            execution_id="e1", test_id="tc1", status="passed", duration_ms=100.5
        )
        assert e.duration_ms == 100.5

    def test_failed(self) -> None:
        e = TestExecutionFailed(execution_id="e1", test_id="tc1", error="assertion failed")
        assert e.error == "assertion failed"

    def test_failed_default_error(self) -> None:
        e = TestExecutionFailed(execution_id="e1", test_id="tc1")
        assert e.error == ""


class TestSuiteEvents:
    def test_suite_registered(self) -> None:
        e = SuiteRegistered(suite_id="s1", name="suite one", test_count=5)
        assert e.event_type == "eaip.quality.suite.registered"
        assert e.test_count == 5


class TestQualityGateEvents:
    def test_evaluated(self) -> None:
        e = QualityGateEvaluated(gate_id="g1", status="pass", condition_count=3)
        assert e.condition_count == 3

    def test_passed(self) -> None:
        e = QualityGatePassed(gate_id="g1", name="gate one")
        assert e.event_type == "eaip.quality.gate.passed"

    def test_failed(self) -> None:
        e = QualityGateFailed(gate_id="g1", name="gate one", reason="pass rate too low")
        assert e.reason == "pass rate too low"

    def test_failed_default_reason(self) -> None:
        e = QualityGateFailed(gate_id="g1", name="gate one")
        assert e.reason == ""


class TestCoverageEvents:
    def test_coverage_reported(self) -> None:
        e = CoverageReported(report_id="cr1", component="comp1", line_rate=0.85, branch_rate=0.75)
        assert e.event_type == "eaip.quality.coverage.reported"
        assert e.line_rate == 0.85


class TestRegressionEvents:
    def test_detected(self) -> None:
        e = RegressionDetected(regression_id="rr1", component="comp1", change_count=3)
        assert e.event_type == "eaip.quality.regression.detected"
        assert e.change_count == 3

    def test_cleared(self) -> None:
        e = RegressionCleared(regression_id="rr1", component="comp1")
        assert e.event_type == "eaip.quality.regression.cleared"
