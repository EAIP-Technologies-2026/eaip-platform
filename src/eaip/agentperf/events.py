"""Domain events for the agent performance analyzer."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ExecutionRecorded(DomainEvent):
    """Emitted when an agent execution is recorded."""

    event_type: ClassVar[str] = "eaip.agentperf.execution.recorded"

    execution_id: str
    agent_id: str
    task_type: str
    duration_ms: float
    success: bool


class BottleneckDetected(DomainEvent):
    """Emitted when a performance bottleneck is detected."""

    event_type: ClassVar[str] = "eaip.agentperf.bottleneck.detected"

    report_id: str
    agent_id: str
    metric: str
    actual_value: float
    threshold: float


class AgentComparisonCompleted(DomainEvent):
    """Emitted when an agent comparison is completed."""

    event_type: ClassVar[str] = "eaip.agentperf.comparison.completed"

    comparison_id: str
    agent_ids: tuple[str, ...]
    metric: str


__all__ = [
    "AgentComparisonCompleted",
    "BottleneckDetected",
    "ExecutionRecorded",
]
