"""Domain events for the quality & testing framework."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class TestCaseRegistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.quality.test_case.registered"
    test_id: str
    name: str
    type: str
    component: str


class TestCaseUnregistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.quality.test_case.unregistered"
    test_id: str


class TestExecutionStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.quality.test_execution.started"
    execution_id: str
    test_id: str
    suite_id: str = Field(default="")


class TestExecutionCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.quality.test_execution.completed"
    execution_id: str
    test_id: str
    status: str
    duration_ms: float


class TestExecutionFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.quality.test_execution.failed"
    execution_id: str
    test_id: str
    error: str = Field(default="")


class SuiteRegistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.quality.suite.registered"
    suite_id: str
    name: str
    test_count: int


class QualityGateEvaluated(DomainEvent):
    event_type: ClassVar[str] = "eaip.quality.gate.evaluated"
    gate_id: str
    status: str
    condition_count: int


class QualityGatePassed(DomainEvent):
    event_type: ClassVar[str] = "eaip.quality.gate.passed"
    gate_id: str
    name: str


class QualityGateFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.quality.gate.failed"
    gate_id: str
    name: str
    reason: str = Field(default="")


class CoverageReported(DomainEvent):
    event_type: ClassVar[str] = "eaip.quality.coverage.reported"
    report_id: str
    component: str
    line_rate: float
    branch_rate: float


class RegressionDetected(DomainEvent):
    event_type: ClassVar[str] = "eaip.quality.regression.detected"
    regression_id: str
    component: str
    change_count: int


class RegressionCleared(DomainEvent):
    event_type: ClassVar[str] = "eaip.quality.regression.cleared"
    regression_id: str
    component: str
