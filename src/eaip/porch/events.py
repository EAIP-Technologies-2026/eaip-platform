"""Domain events for the pipeline orchestration engine."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class PipelineCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.porch.pipeline.created"

    pipeline_id: str
    name: str


class PipelineStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.porch.pipeline.started"

    pipeline_id: str
    run_id: str


class PipelineCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.porch.pipeline.completed"

    pipeline_id: str
    run_id: str


class PipelineFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.porch.pipeline.failed"

    pipeline_id: str
    run_id: str
    error: str


class StageStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.porch.stage.started"

    pipeline_id: str
    run_id: str
    stage_id: str
    stage_name: str


class StageCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.porch.stage.completed"

    pipeline_id: str
    run_id: str
    stage_id: str
    stage_name: str


class StageFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.porch.stage.failed"

    pipeline_id: str
    run_id: str
    stage_id: str
    stage_name: str
    error: str


__all__ = [
    "PipelineCompleted",
    "PipelineCreated",
    "PipelineFailed",
    "PipelineStarted",
    "StageCompleted",
    "StageFailed",
    "StageStarted",
]
