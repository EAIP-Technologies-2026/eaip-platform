"""Domain events for the performance management framework."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class BenchmarkCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.perf.benchmark.created"
    benchmark_id: str
    name: str
    component: str
    metric_type: str


class BenchmarkRunCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.perf.benchmark_run.completed"
    run_id: str
    benchmark_id: str
    result_value: float
    passed: bool
    duration_ms: float


class BenchmarkRunFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.perf.benchmark_run.failed"
    run_id: str
    benchmark_id: str
    error: str = Field(default="")


class LoadTestStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.perf.load_test.started"
    result_id: str
    scenario_id: str
    target_component: str


class LoadTestCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.perf.load_test.completed"
    result_id: str
    scenario_id: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    error_rate: float


class RegressionDetected(DomainEvent):
    event_type: ClassVar[str] = "eaip.perf.regression.detected"
    regression_id: str
    benchmark_id: str
    direction: str
    severity: str
    change_percent: float


class RegressionResolved(DomainEvent):
    event_type: ClassVar[str] = "eaip.perf.regression.resolved"
    regression_id: str
    benchmark_id: str


class FalsePositiveMarked(DomainEvent):
    event_type: ClassVar[str] = "eaip.perf.regression.false_positive"
    regression_id: str
    benchmark_id: str
