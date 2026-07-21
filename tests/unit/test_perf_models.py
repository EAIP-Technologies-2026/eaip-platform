"""Tests for :mod:`eaip.perf.models`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.perf.models import (
    BenchmarkDefinition,
    BenchmarkRun,
    BenchmarkRunStatus,
    LoadTestResult,
    LoadTestScenario,
    MetricType,
    PerfConfig,
    PerformanceRegression,
    RegressionDirection,
    RegressionSeverity,
    RegressionStatus,
)

BenchmarkDefinition.__test__ = False
BenchmarkRun.__test__ = False
LoadTestScenario.__test__ = False
LoadTestResult.__test__ = False
PerformanceRegression.__test__ = False


class TestMetricType:
    def test_values(self) -> None:
        assert MetricType.LATENCY.value == "latency"
        assert MetricType.THROUGHPUT.value == "throughput"
        assert MetricType.MEMORY.value == "memory"
        assert MetricType.CPU.value == "cpu"
        assert MetricType.IO.value == "io"


class TestBenchmarkRunStatus:
    def test_values(self) -> None:
        assert BenchmarkRunStatus.PENDING.value == "pending"
        assert BenchmarkRunStatus.RUNNING.value == "running"
        assert BenchmarkRunStatus.COMPLETED.value == "completed"
        assert BenchmarkRunStatus.FAILED.value == "failed"


class TestRegressionDirection:
    def test_values(self) -> None:
        assert RegressionDirection.IMPROVEMENT.value == "improvement"
        assert RegressionDirection.REGRESSION.value == "regression"
        assert RegressionDirection.UNCHANGED.value == "unchanged"


class TestRegressionSeverity:
    def test_values(self) -> None:
        assert RegressionSeverity.LOW.value == "low"
        assert RegressionSeverity.MEDIUM.value == "medium"
        assert RegressionSeverity.HIGH.value == "high"
        assert RegressionSeverity.CRITICAL.value == "critical"


class TestRegressionStatus:
    def test_values(self) -> None:
        assert RegressionStatus.OPEN.value == "open"
        assert RegressionStatus.ACKNOWLEDGED.value == "acknowledged"
        assert RegressionStatus.RESOLVED.value == "resolved"
        assert RegressionStatus.FALSE_POSITIVE.value == "false_positive"


class TestBenchmarkDefinition:
    def test_create_minimal(self) -> None:
        b = BenchmarkDefinition(
            id="b1",
            name="p50 latency",
            component="api",
            metric_type=MetricType.LATENCY,
            target_value=200.0,
        )
        assert b.id == "b1"
        assert b.name == "p50 latency"
        assert b.metric_type is MetricType.LATENCY
        assert b.target_value == 200.0
        assert b.threshold_value == 0.0
        assert b.enabled is True

    def test_create_full(self) -> None:
        b = BenchmarkDefinition(
            id="b2",
            name="throughput",
            description="API throughput benchmark",
            component="api-gateway",
            metric_type=MetricType.THROUGHPUT,
            target_value=1000.0,
            threshold_value=800.0,
            unit="req/s",
            tags=("critical", "api"),
            metadata={"env": "prod"},
            enabled=False,
        )
        assert b.threshold_value == 800.0
        assert b.tags == ("critical", "api")
        assert b.enabled is False

    def test_frozen(self) -> None:
        b = BenchmarkDefinition(
            id="b3", name="test", component="c", metric_type=MetricType.CPU, target_value=50.0
        )
        with pytest.raises(ValidationError):
            b.name = "changed"


class TestBenchmarkRun:
    def test_create_minimal(self) -> None:
        r = BenchmarkRun(id="r1", benchmark_id="b1")
        assert r.status is BenchmarkRunStatus.PENDING
        assert r.duration_ms == 0.0
        assert r.result_value == 0.0
        assert r.passed is False
        assert r.error == ""

    def test_create_completed(self) -> None:
        now = datetime.now(UTC)
        r = BenchmarkRun(
            id="r2",
            benchmark_id="b1",
            status=BenchmarkRunStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            duration_ms=150.5,
            result_value=95.0,
            passed=True,
        )
        assert r.duration_ms == 150.5
        assert r.result_value == 95.0
        assert r.passed is True

    def test_frozen(self) -> None:
        r = BenchmarkRun(id="r3", benchmark_id="b1")
        with pytest.raises(ValidationError):
            r.status = BenchmarkRunStatus.RUNNING


class TestLoadTestScenario:
    def test_create_minimal(self) -> None:
        s = LoadTestScenario(id="s1", name="basic", target_component="api")
        assert s.concurrency_level == 1
        assert s.duration_seconds == 30
        assert s.ramp_up_seconds == 0
        assert s.enabled is True

    def test_create_full(self) -> None:
        s = LoadTestScenario(
            id="s2",
            name="stress",
            description="Stress test",
            target_component="api",
            concurrency_level=50,
            duration_seconds=120,
            ramp_up_seconds=10,
            endpoint_pattern="/api/v1/process",
            request_config={"method": "POST", "body": {"key": "value"}},
            tags=("stress",),
            metadata={"env": "staging"},
            enabled=False,
        )
        assert s.concurrency_level == 50
        assert s.ramp_up_seconds == 10
        assert s.request_config["method"] == "POST"

    def test_invalid_concurrency(self) -> None:
        with pytest.raises(ValidationError):
            LoadTestScenario(id="s3", name="bad", target_component="api", concurrency_level=0)

    def test_frozen(self) -> None:
        s = LoadTestScenario(id="s4", name="test", target_component="api")
        with pytest.raises(ValidationError):
            s.name = "changed"


class TestLoadTestResult:
    def test_create_minimal(self) -> None:
        r = LoadTestResult(id="r1", scenario_id="s1")
        assert r.status is BenchmarkRunStatus.PENDING
        assert r.total_requests == 0
        assert r.error_rate == 0.0

    def test_create_full(self) -> None:
        r = LoadTestResult(
            id="r2",
            scenario_id="s1",
            status=BenchmarkRunStatus.COMPLETED,
            total_requests=1000,
            successful_requests=950,
            failed_requests=50,
            avg_response_time_ms=120.5,
            p50_response_time=100.0,
            p95_response_time=200.0,
            p99_response_time=300.0,
            throughput_reqs_per_sec=500.0,
            error_rate=0.05,
        )
        assert r.successful_requests == 950
        assert r.error_rate == 0.05

    def test_invalid_error_rate(self) -> None:
        with pytest.raises(ValidationError):
            LoadTestResult(id="r3", scenario_id="s1", error_rate=1.5)

    def test_frozen(self) -> None:
        r = LoadTestResult(id="r4", scenario_id="s1")
        with pytest.raises(ValidationError):
            r.total_requests = 100


class TestPerformanceRegression:
    def test_create_minimal(self) -> None:
        p = PerformanceRegression(
            id="p1",
            benchmark_id="b1",
            baseline_run_id="br1",
            current_run_id="cr1",
            metric_type=MetricType.LATENCY,
        )
        assert p.direction is RegressionDirection.UNCHANGED
        assert p.severity is RegressionSeverity.LOW
        assert p.status is RegressionStatus.OPEN

    def test_create_full(self) -> None:
        p = PerformanceRegression(
            id="p2",
            benchmark_id="b1",
            baseline_run_id="br1",
            current_run_id="cr1",
            metric_type=MetricType.THROUGHPUT,
            baseline_value=1000.0,
            current_value=500.0,
            change_percent=-50.0,
            direction=RegressionDirection.REGRESSION,
            severity=RegressionSeverity.CRITICAL,
            status=RegressionStatus.ACKNOWLEDGED,
        )
        assert p.change_percent == -50.0
        assert p.severity is RegressionSeverity.CRITICAL

    def test_frozen(self) -> None:
        p = PerformanceRegression(
            id="p3",
            benchmark_id="b1",
            baseline_run_id="br1",
            current_run_id="cr1",
            metric_type=MetricType.CPU,
        )
        with pytest.raises(ValidationError):
            p.status = RegressionStatus.RESOLVED


class TestPerfConfig:
    def test_defaults(self) -> None:
        c = PerfConfig()
        assert c.benchmark_interval_hours == 24
        assert c.regression_threshold_percent == 10.0
        assert c.max_concurrent_runs == 5
        assert c.history_retention_days == 90
        assert c.enable_auto_benchmark is True

    def test_custom(self) -> None:
        c = PerfConfig(
            benchmark_interval_hours=12,
            regression_threshold_percent=5.0,
            max_concurrent_runs=10,
            history_retention_days=30,
            enable_auto_benchmark=False,
        )
        assert c.benchmark_interval_hours == 12
        assert c.max_concurrent_runs == 10

    def test_invalid_interval(self) -> None:
        with pytest.raises(ValidationError):
            PerfConfig(benchmark_interval_hours=0)

    def test_frozen(self) -> None:
        c = PerfConfig()
        with pytest.raises(ValidationError):
            c.benchmark_interval_hours = 48
