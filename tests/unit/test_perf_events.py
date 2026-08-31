"""Tests for :mod:`eaip.perf.events`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.perf.events import (
    BenchmarkCreated,
    BenchmarkRunCompleted,
    BenchmarkRunFailed,
    FalsePositiveMarked,
    LoadTestCompleted,
    LoadTestStarted,
    RegressionDetected,
    RegressionResolved,
)

BenchmarkCreated.__test__ = False
BenchmarkRunCompleted.__test__ = False
BenchmarkRunFailed.__test__ = False
LoadTestStarted.__test__ = False
LoadTestCompleted.__test__ = False
RegressionDetected.__test__ = False
RegressionResolved.__test__ = False
FalsePositiveMarked.__test__ = False


class TestBenchmarkEvents:
    def test_created(self) -> None:
        e = BenchmarkCreated(benchmark_id="b1", name="p50", component="api", metric_type="latency")
        assert e.event_type == "eaip.perf.benchmark.created"
        assert e.benchmark_id == "b1"
        assert e.name == "p50"
        assert e.component == "api"

    def test_run_completed(self) -> None:
        e = BenchmarkRunCompleted(
            run_id="r1", benchmark_id="b1", result_value=95.0, passed=True, duration_ms=150.5
        )
        assert e.event_type == "eaip.perf.benchmark_run.completed"
        assert e.result_value == 95.0
        assert e.passed is True

    def test_run_failed(self) -> None:
        e = BenchmarkRunFailed(run_id="r1", benchmark_id="b1", error="timeout")
        assert e.event_type == "eaip.perf.benchmark_run.failed"
        assert e.error == "timeout"

    def test_run_failed_default_error(self) -> None:
        e = BenchmarkRunFailed(run_id="r1", benchmark_id="b1")
        assert e.error == ""


class TestLoadTestEvents:
    def test_started(self) -> None:
        e = LoadTestStarted(result_id="r1", scenario_id="s1", target_component="api")
        assert e.event_type == "eaip.perf.load_test.started"
        assert e.scenario_id == "s1"

    def test_completed(self) -> None:
        e = LoadTestCompleted(
            result_id="r1",
            scenario_id="s1",
            total_requests=1000,
            successful_requests=950,
            failed_requests=50,
            avg_response_time_ms=120.5,
            error_rate=0.05,
        )
        assert e.total_requests == 1000
        assert e.error_rate == 0.05


class TestRegressionEvents:
    def test_detected(self) -> None:
        e = RegressionDetected(
            regression_id="p1",
            benchmark_id="b1",
            direction="regression",
            severity="critical",
            change_percent=50.0,
        )
        assert e.event_type == "eaip.perf.regression.detected"
        assert e.change_percent == 50.0

    def test_resolved(self) -> None:
        e = RegressionResolved(regression_id="p1", benchmark_id="b1")
        assert e.event_type == "eaip.perf.regression.resolved"
        assert e.benchmark_id == "b1"

    def test_false_positive(self) -> None:
        e = FalsePositiveMarked(regression_id="p1", benchmark_id="b1")
        assert e.event_type == "eaip.perf.regression.false_positive"


class TestEventImmutability:
    def test_benchmark_created_frozen(self) -> None:
        e = BenchmarkCreated(benchmark_id="b1", name="p50", component="api", metric_type="latency")
        with pytest.raises(ValidationError):
            e.benchmark_id = "changed"

    def test_load_test_started_frozen(self) -> None:
        e = LoadTestStarted(result_id="r1", scenario_id="s1", target_component="api")
        with pytest.raises(ValidationError):
            e.scenario_id = "changed"

    def test_regression_detected_frozen(self) -> None:
        e = RegressionDetected(
            regression_id="p1",
            benchmark_id="b1",
            direction="regression",
            severity="high",
            change_percent=25.0,
        )
        with pytest.raises(ValidationError):
            e.direction = "improvement"


class TestEventOccurredAt:
    def test_benchmark_created_has_timestamp(self) -> None:
        e = BenchmarkCreated(benchmark_id="b1", name="p50", component="api", metric_type="latency")
        assert e.occurred_at is not None

    def test_regression_detected_has_timestamp(self) -> None:
        e = RegressionDetected(
            regression_id="p1",
            benchmark_id="b1",
            direction="regression",
            severity="low",
            change_percent=5.0,
        )
        assert e.occurred_at is not None
