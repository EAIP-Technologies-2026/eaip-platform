from __future__ import annotations

from typing import ClassVar

from eaip.datapipeline.models import (
    DataSink,
    DataSource,
    Pipeline,
    PipelineExecution,
    PipelineStep,
)
from eaip.events.event import DomainEvent


class SourceRegistered(DomainEvent):
    event_type: ClassVar[str] = "datapipeline.source.registered"
    source: DataSource


class SourceUnregistered(DomainEvent):
    event_type: ClassVar[str] = "datapipeline.source.unregistered"
    source_id: str
    source_name: str


class SinkRegistered(DomainEvent):
    event_type: ClassVar[str] = "datapipeline.sink.registered"
    sink: DataSink


class SinkUnregistered(DomainEvent):
    event_type: ClassVar[str] = "datapipeline.sink.unregistered"
    sink_id: str
    sink_name: str


class PipelineRegistered(DomainEvent):
    event_type: ClassVar[str] = "datapipeline.pipeline.registered"
    pipeline: Pipeline


class PipelineUnregistered(DomainEvent):
    event_type: ClassVar[str] = "datapipeline.pipeline.unregistered"
    pipeline_id: str
    pipeline_name: str


class PipelineExecutionStarted(DomainEvent):
    event_type: ClassVar[str] = "datapipeline.pipeline.execution.started"
    execution: PipelineExecution


class PipelineExecutionCompleted(DomainEvent):
    event_type: ClassVar[str] = "datapipeline.pipeline.execution.completed"
    execution: PipelineExecution


class PipelineExecutionFailed(DomainEvent):
    event_type: ClassVar[str] = "datapipeline.pipeline.execution.failed"
    execution: PipelineExecution
    error: str


class PipelineStepCompleted(DomainEvent):
    event_type: ClassVar[str] = "datapipeline.pipeline.step.completed"
    execution_id: str
    step: PipelineStep
    records_processed: int
    duration_ms: float


class PipelineStepFailed(DomainEvent):
    event_type: ClassVar[str] = "datapipeline.pipeline.step.failed"
    execution_id: str
    step: PipelineStep
    error: str
    attempt: int


class PipelineScheduled(DomainEvent):
    event_type: ClassVar[str] = "datapipeline.pipeline.scheduled"
    pipeline_id: str
    cron_expression: str


__all__ = [
    "PipelineExecutionCompleted",
    "PipelineExecutionFailed",
    "PipelineExecutionStarted",
    "PipelineRegistered",
    "PipelineScheduled",
    "PipelineStepCompleted",
    "PipelineStepFailed",
    "PipelineUnregistered",
    "SinkRegistered",
    "SinkUnregistered",
    "SourceRegistered",
    "SourceUnregistered",
]
