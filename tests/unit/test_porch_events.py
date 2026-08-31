"""Tests for porch domain events."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.porch.events import (
    PipelineCompleted,
    PipelineCreated,
    PipelineFailed,
    PipelineStarted,
    StageCompleted,
    StageFailed,
    StageStarted,
)


class TestPipelineCreated:
    def test_event_type(self) -> None:
        event = PipelineCreated(pipeline_id="p1", name="CI")
        assert event.event_type == "eaip.porch.pipeline.created"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = PipelineCreated(pipeline_id="p1", name="CI")
        assert event.pipeline_id == "p1"
        assert event.name == "CI"


class TestPipelineStarted:
    def test_event_type(self) -> None:
        event = PipelineStarted(pipeline_id="p1", run_id="r1")
        assert event.event_type == "eaip.porch.pipeline.started"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = PipelineStarted(pipeline_id="p1", run_id="r1")
        assert event.pipeline_id == "p1"
        assert event.run_id == "r1"


class TestPipelineCompleted:
    def test_event_type(self) -> None:
        event = PipelineCompleted(pipeline_id="p1", run_id="r1")
        assert event.event_type == "eaip.porch.pipeline.completed"
        assert isinstance(event, DomainEvent)


class TestPipelineFailed:
    def test_event_type(self) -> None:
        event = PipelineFailed(pipeline_id="p1", run_id="r1", error="Build error")
        assert event.event_type == "eaip.porch.pipeline.failed"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = PipelineFailed(pipeline_id="p1", run_id="r1", error="Build error")
        assert event.error == "Build error"


class TestStageStarted:
    def test_event_type(self) -> None:
        event = StageStarted(pipeline_id="p1", run_id="r1", stage_id="st1", stage_name="Build")
        assert event.event_type == "eaip.porch.stage.started"
        assert isinstance(event, DomainEvent)


class TestStageCompleted:
    def test_event_type(self) -> None:
        event = StageCompleted(pipeline_id="p1", run_id="r1", stage_id="st1", stage_name="Build")
        assert event.event_type == "eaip.porch.stage.completed"
        assert isinstance(event, DomainEvent)


class TestStageFailed:
    def test_event_type(self) -> None:
        event = StageFailed(
            pipeline_id="p1",
            run_id="r1",
            stage_id="st1",
            stage_name="Build",
            error="Compile error",
        )
        assert event.event_type == "eaip.porch.stage.failed"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = StageFailed(
            pipeline_id="p1",
            run_id="r1",
            stage_id="st1",
            stage_name="Build",
            error="Compile error",
        )
        assert event.error == "Compile error"


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(PipelineCreated, DomainEvent)
        assert issubclass(PipelineStarted, DomainEvent)
        assert issubclass(PipelineCompleted, DomainEvent)
        assert issubclass(PipelineFailed, DomainEvent)
        assert issubclass(StageStarted, DomainEvent)
        assert issubclass(StageCompleted, DomainEvent)
        assert issubclass(StageFailed, DomainEvent)
