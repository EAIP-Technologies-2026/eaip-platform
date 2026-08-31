"""Domain events for the model fallback subsystem."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent
from eaip.model_fallback.models import (
    DegradationLevel,
    FallbackExecutionStatus,
)


class FallbackConfigCreated(DomainEvent):
    """Emitted when a fallback configuration is created."""

    event_type: ClassVar[str] = "eaip.model_fallback.config.created"

    config_id: str
    name: str


class FallbackConfigUpdated(DomainEvent):
    """Emitted when a fallback configuration is updated."""

    event_type: ClassVar[str] = "eaip.model_fallback.config.updated"

    config_id: str
    name: str


class FallbackConfigDeleted(DomainEvent):
    """Emitted when a fallback configuration is deleted."""

    event_type: ClassVar[str] = "eaip.model_fallback.config.deleted"

    config_id: str
    name: str


class FallbackChainExecuted(DomainEvent):
    """Emitted when a fallback chain is executed."""

    event_type: ClassVar[str] = "eaip.model_fallback.chain.executed"

    chain_id: str
    execution_id: str
    status: FallbackExecutionStatus
    duration_ms: float
    degradation_level: DegradationLevel


class FallbackStepStarted(DomainEvent):
    """Emitted when a fallback step begins."""

    event_type: ClassVar[str] = "eaip.model_fallback.step.started"

    chain_id: str
    execution_id: str
    step_name: str
    model_id: str


class FallbackStepSkipped(DomainEvent):
    """Emitted when a fallback step is skipped."""

    event_type: ClassVar[str] = "eaip.model_fallback.step.skipped"

    chain_id: str
    execution_id: str
    step_name: str
    model_id: str
    reason: str


class FallbackStepCompleted(DomainEvent):
    """Emitted when a fallback step completes successfully."""

    event_type: ClassVar[str] = "eaip.model_fallback.step.completed"

    chain_id: str
    execution_id: str
    step_name: str
    model_id: str
    duration_ms: float


class FallbackStepFailed(DomainEvent):
    """Emitted when a fallback step fails."""

    event_type: ClassVar[str] = "eaip.model_fallback.step.failed"

    chain_id: str
    execution_id: str
    step_name: str
    model_id: str
    error: str
    duration_ms: float


class FallbackExecutionCompleted(DomainEvent):
    """Emitted when a fallback chain execution completes successfully."""

    event_type: ClassVar[str] = "eaip.model_fallback.execution.completed"

    chain_id: str
    execution_id: str
    final_model_id: str | None
    duration_ms: float
    steps_attempted: int


class FallbackExecutionFailed(DomainEvent):
    """Emitted when a fallback chain execution fails."""

    event_type: ClassVar[str] = "eaip.model_fallback.execution.failed"

    chain_id: str
    execution_id: str
    error: str
    duration_ms: float
    steps_attempted: int


class FallbackTriggered(DomainEvent):
    """Emitted when a fallback is triggered."""

    event_type: ClassVar[str] = "eaip.model_fallback.triggered"

    chain_id: str
    execution_id: str
    from_model_id: str
    to_model_id: str
    reason: str


class FallbackRecoverySucceeded(DomainEvent):
    """Emitted when recovery from a fallback state succeeds."""

    event_type: ClassVar[str] = "eaip.model_fallback.recovery.succeeded"

    chain_id: str
    execution_id: str
    model_id: str


class FallbackRecoveryFailed(DomainEvent):
    """Emitted when recovery from a fallback state fails."""

    event_type: ClassVar[str] = "eaip.model_fallback.recovery.failed"

    chain_id: str
    execution_id: str
    model_id: str
    error: str


class FallbackMetricsCollected(DomainEvent):
    """Emitted when fallback metrics are collected."""

    event_type: ClassVar[str] = "eaip.model_fallback.metrics.collected"

    chain_id: str
    metrics: dict[str, Any]


class DegradationLevelChanged(DomainEvent):
    """Emitted when the degradation level changes."""

    event_type: ClassVar[str] = "eaip.model_fallback.degradation.changed"

    chain_id: str
    execution_id: str
    previous_level: DegradationLevel
    current_level: DegradationLevel


class FallbackHistoryLogged(DomainEvent):
    """Emitted when a fallback history entry is logged."""

    event_type: ClassVar[str] = "eaip.model_fallback.history.logged"

    entry_id: str
    execution_id: str
    chain_id: str
    event_type_name: str


__all__ = [
    "DegradationLevelChanged",
    "FallbackChainExecuted",
    "FallbackConfigCreated",
    "FallbackConfigDeleted",
    "FallbackConfigUpdated",
    "FallbackExecutionCompleted",
    "FallbackExecutionFailed",
    "FallbackHistoryLogged",
    "FallbackMetricsCollected",
    "FallbackRecoveryFailed",
    "FallbackRecoverySucceeded",
    "FallbackStepCompleted",
    "FallbackStepFailed",
    "FallbackStepSkipped",
    "FallbackStepStarted",
    "FallbackTriggered",
]
