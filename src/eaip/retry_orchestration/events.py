"""Domain events for retry orchestration - policy, execution, circuit breaker, metrics."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent
from eaip.retry_orchestration.models import (
    RetryExecution,
    RetryMetrics,
    RetryPolicy,
    RetryState,
)


class RetryPolicyCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.policy.created"
    policy: RetryPolicy


class RetryPolicyUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.policy.updated"
    policy: RetryPolicy


class RetryPolicyDeleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.policy.deleted"
    policy_id: str = ""
    policy_name: str = ""


class RetryExecutionStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.execution.started"
    execution: RetryExecution


class RetryExecutionCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.execution.completed"
    execution: RetryExecution
    result: str = ""


class RetryExecutionFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.execution.failed"
    execution: RetryExecution
    error: str = ""


class RetryAttemptScheduled(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.attempt.scheduled"
    execution_id: str = ""
    policy_id: str = ""
    attempt: int = 0
    delay_seconds: float = 0.0
    scheduled_at: str = ""


class RetryAttemptStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.attempt.started"
    execution_id: str = ""
    policy_id: str = ""
    attempt: int = 0
    state: RetryState | None = None


class RetryAttemptCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.attempt.completed"
    execution_id: str = ""
    policy_id: str = ""
    attempt: int = 0
    duration_ms: float = 0.0
    result: str = ""


class RetryAttemptFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.attempt.failed"
    execution_id: str = ""
    policy_id: str = ""
    attempt: int = 0
    error: str = ""
    will_retry: bool = False
    delay_seconds: float = 0.0


class RetryExhausted(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.exhausted"
    execution_id: str = ""
    policy_id: str = ""
    target: str = ""
    total_attempts: int = 0
    last_error: str = ""


class CircuitBreakerTripped(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.circuit_breaker.tripped"
    policy_id: str = ""
    failure_count: int = 0
    threshold: int = 0
    opened_at: str = ""


class CircuitBreakerHalfOpened(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.circuit_breaker.half_opened"
    policy_id: str = ""
    open_duration_seconds: float = 0.0


class CircuitBreakerReset(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.circuit_breaker.reset"
    policy_id: str = ""
    success_count: int = 0


class RetryMetricsCollected(DomainEvent):
    event_type: ClassVar[str] = "eaip.retry_orchestration.metrics.collected"
    metrics: RetryMetrics


__all__ = [
    "CircuitBreakerHalfOpened",
    "CircuitBreakerReset",
    "CircuitBreakerTripped",
    "RetryAttemptCompleted",
    "RetryAttemptFailed",
    "RetryAttemptScheduled",
    "RetryAttemptStarted",
    "RetryExecutionCompleted",
    "RetryExecutionFailed",
    "RetryExecutionStarted",
    "RetryExhausted",
    "RetryMetricsCollected",
    "RetryPolicyCreated",
    "RetryPolicyDeleted",
    "RetryPolicyUpdated",
]
