"""Tests for :mod:`eaip.quality.models`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.quality.models import (
    CoverageReport,
    MetricOperator,
    MetricType,
    PerformanceBenchmark,
    Priority,
    QualityCondition,
    QualityConfig,
    QualityGate,
    QualityGateStatus,
    RegressionChange,
    RegressionResult,
    RegressionStatus,
    TestCase,
    TestCaseStatus,
    TestCaseType,
    TestExecution,
    TestExecutionStatus,
    TestSuite,
)

# Prevent pytest from collecting source classes as test classes
TestCase.__test__ = False
TestSuite.__test__ = False
TestExecution.__test__ = False
TestCaseStatus.__test__ = False
TestCaseType.__test__ = False
TestExecutionStatus.__test__ = False


class TestTestCase:
    def test_create_minimal(self) -> None:
        tc = TestCase(id="tc1", name="test one")
        assert tc.id == "tc1"
        assert tc.name == "test one"
        assert tc.type is TestCaseType.UNIT
        assert tc.status is TestCaseStatus.DRAFT
        assert tc.priority is Priority.MEDIUM

    def test_create_full(self) -> None:
        tc = TestCase(
            id="tc2",
            name="test two",
            description="desc",
            type=TestCaseType.INTEGRATION,
            status=TestCaseStatus.ACTIVE,
            component="comp1",
            input_data={"x": 1},
            expected_output={"y": 2},
            assertions=("eq",),
            tags=("smoke",),
            metadata={"env": "test"},
            author="author1",
            priority=Priority.HIGH,
        )
        assert tc.component == "comp1"
        assert tc.assertions == ("eq",)
        assert tc.author == "author1"

    def test_frozen(self) -> None:
        tc = TestCase(id="tc3", name="test three")
        with pytest.raises(ValidationError):
            tc.name = "changed"

    def test_default_priority(self) -> None:
        tc = TestCase(id="tc4", name="test four")
        assert tc.priority is Priority.MEDIUM

    def test_all_types(self) -> None:
        assert TestCaseType.UNIT.value == "unit"
        assert TestCaseType.INTEGRATION.value == "integration"
        assert TestCaseType.E2E.value == "e2e"
        assert TestCaseType.REGRESSION.value == "regression"
        assert TestCaseType.PERFORMANCE.value == "performance"

    def test_all_statuses(self) -> None:
        assert TestCaseStatus.ACTIVE.value == "active"
        assert TestCaseStatus.DEPRECATED.value == "deprecated"
        assert TestCaseStatus.DRAFT.value == "draft"


class TestTestSuite:
    def test_create_minimal(self) -> None:
        s = TestSuite(id="s1", name="suite one")
        assert s.id == "s1"
        assert s.test_ids == ()
        assert s.parallel_execution is False
        assert s.timeout_seconds == 300

    def test_create_with_tests(self) -> None:
        s = TestSuite(id="s2", name="suite two", test_ids=("tc1", "tc2"), parallel_execution=True)
        assert s.test_ids == ("tc1", "tc2")
        assert s.parallel_execution is True

    def test_frozen(self) -> None:
        s = TestSuite(id="s3", name="suite three")
        with pytest.raises(ValidationError):
            s.name = "changed"

    def test_empty_test_ids(self) -> None:
        s = TestSuite(id="s4", name="empty suite")
        assert s.test_ids == ()


class TestTestExecution:
    def test_create_minimal(self) -> None:
        e = TestExecution(id="e1", test_id="tc1")
        assert e.status is TestExecutionStatus.PENDING
        assert e.duration_ms == 0.0
        assert e.error == ""

    def test_create_completed(self) -> None:
        now = datetime.now(UTC)
        e = TestExecution(
            id="e2",
            test_id="tc1",
            status=TestExecutionStatus.PASSED,
            started_at=now,
            completed_at=now,
            duration_ms=100.5,
            result={"output": "ok"},
            assertion_results={"eq": True},
        )
        assert e.duration_ms == 100.5
        assert e.assertion_results == {"eq": True}

    def test_all_statuses(self) -> None:
        values = {s.value for s in TestExecutionStatus}
        assert "pending" in values
        assert "running" in values
        assert "passed" in values
        assert "failed" in values
        assert "skipped" in values
        assert "error" in values

    def test_frozen(self) -> None:
        e = TestExecution(id="e3", test_id="tc1")
        with pytest.raises(ValidationError):
            e.status = TestExecutionStatus.RUNNING


class TestQualityCondition:
    def test_create(self) -> None:
        c = QualityCondition(metric="pass_rate", operator=MetricOperator.GTE, value=0.9)
        assert c.metric == "pass_rate"
        assert c.operator is MetricOperator.GTE
        assert c.value == 0.9

    def test_all_operators(self) -> None:
        assert MetricOperator.GT.value == "gt"
        assert MetricOperator.GTE.value == "gte"
        assert MetricOperator.LT.value == "lt"
        assert MetricOperator.LTE.value == "lte"
        assert MetricOperator.EQ.value == "eq"
        assert MetricOperator.NEQ.value == "neq"


class TestQualityGate:
    def test_create_minimal(self) -> None:
        g = QualityGate(id="g1", name="gate one")
        assert g.status is QualityGateStatus.PENDING
        assert g.conditions == ()

    def test_create_with_conditions(self) -> None:
        c = QualityCondition(metric="pass_rate", operator=MetricOperator.GTE, value=0.9)
        g = QualityGate(id="g2", name="gate two", conditions=(c,))
        assert len(g.conditions) == 1

    def test_status_values(self) -> None:
        assert QualityGateStatus.PASS.value == "pass"
        assert QualityGateStatus.FAIL.value == "fail"
        assert QualityGateStatus.PENDING.value == "pending"

    def test_frozen(self) -> None:
        g = QualityGate(id="g3", name="gate three")
        with pytest.raises(ValidationError):
            g.status = QualityGateStatus.PASS


class TestCoverageReport:
    def test_create_minimal(self) -> None:
        r = CoverageReport(id="cr1", component="comp1")
        assert r.line_rate == 0.0
        assert r.total_lines == 0
        assert r.uncovered_lines == ()

    def test_create_full(self) -> None:
        r = CoverageReport(
            id="cr2",
            component="comp1",
            line_rate=0.85,
            branch_rate=0.75,
            function_rate=0.9,
            uncovered_lines=(10, 20, 30),
            total_lines=100,
            covered_lines=85,
        )
        assert r.line_rate == 0.85
        assert len(r.uncovered_lines) == 3

    def test_invalid_rates(self) -> None:
        with pytest.raises(ValidationError):
            CoverageReport(id="cr3", component="comp1", line_rate=1.5)
        with pytest.raises(ValidationError):
            CoverageReport(id="cr4", component="comp1", line_rate=-0.1)

    def test_frozen(self) -> None:
        r = CoverageReport(id="cr5", component="comp1")
        with pytest.raises(ValidationError):
            r.line_rate = 0.5


class TestRegressionModels:
    def test_regression_change(self) -> None:
        c = RegressionChange(
            test_id="tc1",
            test_name="test one",
            baseline_status="passed",
            current_status="failed",
            baseline_duration_ms=100.0,
            current_duration_ms=200.0,
            delta_ms=100.0,
        )
        assert c.delta_ms == 100.0

    def test_regression_result_clean(self) -> None:
        r = RegressionResult(id="rr1", baseline_id="b1", current_id="c1", component="comp1")
        assert r.status is RegressionStatus.CLEAN
        assert r.changes == ()

    def test_regression_result_with_changes(self) -> None:
        c = RegressionChange(
            test_id="tc1", test_name="t1", baseline_status="passed", current_status="failed"
        )
        r = RegressionResult(
            id="rr2",
            baseline_id="b1",
            current_id="c1",
            component="comp1",
            status=RegressionStatus.REGRESSION,
            changes=(c,),
        )
        assert r.status is RegressionStatus.REGRESSION

    def test_regression_status_values(self) -> None:
        assert RegressionStatus.CLEAN.value == "clean"
        assert RegressionStatus.REGRESSION.value == "regression"
        assert RegressionStatus.IMPROVED.value == "improved"


class TestPerformanceBenchmark:
    def test_create_minimal(self) -> None:
        b = PerformanceBenchmark(
            id="pb1",
            name="p90",
            component="api",
            metric=MetricType.RESPONSE_TIME,
            value=200.0,
            unit="ms",
            threshold=300.0,
        )
        assert b.status is QualityGateStatus.PASS

    def test_metric_values(self) -> None:
        assert MetricType.RESPONSE_TIME.value == "response_time"
        assert MetricType.THROUGHPUT.value == "throughput"
        assert MetricType.MEMORY.value == "memory"
        assert MetricType.CPU.value == "cpu"

    def test_frozen(self) -> None:
        b = PerformanceBenchmark(
            id="pb2",
            name="p50",
            component="api",
            metric=MetricType.RESPONSE_TIME,
            value=100.0,
            unit="ms",
            threshold=200.0,
        )
        with pytest.raises(ValidationError):
            b.value = 150.0


class TestQualityConfig:
    def test_defaults(self) -> None:
        c = QualityConfig()
        assert c.default_timeout_seconds == 300
        assert c.max_retries == 3
        assert c.enable_parallel_execution is False
        assert c.coverage_threshold == 0.8
        assert c.enable_regression_detection is True
        assert c.history_retention_days == 90

    def test_custom(self) -> None:
        c = QualityConfig(
            default_timeout_seconds=600,
            max_retries=5,
            enable_parallel_execution=True,
            coverage_threshold=0.9,
            enable_regression_detection=False,
            history_retention_days=180,
        )
        assert c.default_timeout_seconds == 600
        assert c.coverage_threshold == 0.9

    def test_invalid_threshold(self) -> None:
        with pytest.raises(ValidationError):
            QualityConfig(coverage_threshold=1.5)
        with pytest.raises(ValidationError):
            QualityConfig(coverage_threshold=-0.1)

    def test_frozen(self) -> None:
        c = QualityConfig()
        with pytest.raises(ValidationError):
            c.max_retries = 10
