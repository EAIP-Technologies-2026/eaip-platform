"""Domain events for the CI service."""

from __future__ import annotations

from typing import ClassVar

from eaip.ciservice.models import BuildStatus
from eaip.events.event import DomainEvent


class PipelineCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ciservice.pipeline.created"
    pipeline_id: str
    name: str
    repo_url: str


class BuildStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.ciservice.build.started"
    build_id: str
    pipeline_id: str
    commit_sha: str


class BuildCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.ciservice.build.completed"
    build_id: str
    pipeline_id: str
    status: BuildStatus


class BuildFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.ciservice.build.failed"
    build_id: str
    pipeline_id: str
    reason: str


__all__ = [
    "BuildCompleted",
    "BuildFailed",
    "BuildStarted",
    "PipelineCreated",
]
