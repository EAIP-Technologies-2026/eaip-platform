from __future__ import annotations

import pytest

from eaip.datapipeline.events import (
    PipelineExecutionCompleted,
    PipelineExecutionFailed,
    PipelineExecutionStarted,
    PipelineRegistered,
    PipelineScheduled,
    PipelineStepCompleted,
    PipelineStepFailed,
    PipelineUnregistered,
    SinkRegistered,
    SinkUnregistered,
    SourceRegistered,
    SourceUnregistered,
)
from eaip.datapipeline.models import (
    DataSink,
    DataSource,
    Pipeline,
    PipelineExecution,
    PipelineStep,
    SinkType,
    SourceType,
    StepType,
)


class TestSourceEvents:
    def test_source_registered(self) -> None:
        source = DataSource(id="s1", name="src", type=SourceType.API)
        event = SourceRegistered(source=source)
        assert event.event_type == "datapipeline.source.registered"
        assert event.source.id == "s1"

    def test_source_unregistered(self) -> None:
        event = SourceUnregistered(source_id="s1", source_name="src")
        assert event.event_type == "datapipeline.source.unregistered"
        assert event.source_id == "s1"
        assert event.source_name == "src"


class TestSinkEvents:
    def test_sink_registered(self) -> None:
        sink = DataSink(id="sk1", name="mysink", type=SinkType.FILE)
        event = SinkRegistered(sink=sink)
        assert event.event_type == "datapipeline.sink.registered"
        assert event.sink.id == "sk1"

    def test_sink_unregistered(self) -> None:
        event = SinkUnregistered(sink_id="sk1", sink_name="mysink")
        assert event.event_type == "datapipeline.sink.unregistered"


class TestPipelineEvents:
    def test_pipeline_registered(self) -> None:
        p = Pipeline(id="p1", name="pipe", source_id="s1", sink_id="sk1")
        event = PipelineRegistered(pipeline=p)
        assert event.event_type == "datapipeline.pipeline.registered"
        assert event.pipeline.id == "p1"

    def test_pipeline_unregistered(self) -> None:
        event = PipelineUnregistered(pipeline_id="p1", pipeline_name="pipe")
        assert event.event_type == "datapipeline.pipeline.unregistered"

    def test_pipeline_execution_started(self) -> None:
        exec_ = PipelineExecution(id="e1", pipeline_id="p1")
        event = PipelineExecutionStarted(execution=exec_)
        assert event.event_type == "datapipeline.pipeline.execution.started"

    def test_pipeline_execution_completed(self) -> None:
        exec_ = PipelineExecution(id="e1", pipeline_id="p1", status="completed")
        event = PipelineExecutionCompleted(execution=exec_)
        assert event.event_type == "datapipeline.pipeline.execution.completed"

    def test_pipeline_execution_failed(self) -> None:
        exec_ = PipelineExecution(id="e1", pipeline_id="p1", status="failed")
        event = PipelineExecutionFailed(execution=exec_, error="boom")
        assert event.event_type == "datapipeline.pipeline.execution.failed"
        assert event.error == "boom"

    def test_pipeline_step_completed(self) -> None:
        step = PipelineStep(id="st1", name="xform", type=StepType.TRANSFORM)
        event = PipelineStepCompleted(
            execution_id="e1",
            step=step,
            records_processed=50,
            duration_ms=100.0,
        )
        assert event.event_type == "datapipeline.pipeline.step.completed"
        assert event.records_processed == 50

    def test_pipeline_step_failed(self) -> None:
        step = PipelineStep(id="st1", name="xform", type=StepType.TRANSFORM)
        event = PipelineStepFailed(
            execution_id="e1",
            step=step,
            error="fail",
            attempt=1,
        )
        assert event.event_type == "datapipeline.pipeline.step.failed"
        assert event.error == "fail"

    def test_pipeline_scheduled(self) -> None:
        event = PipelineScheduled(pipeline_id="p1", cron_expression="0 * * * *")
        assert event.event_type == "datapipeline.pipeline.scheduled"
        assert event.cron_expression == "0 * * * *"


class TestEventImmutability:
    def test_events_are_frozen(self) -> None:
        p = Pipeline(id="p1", name="pipe", source_id="s1", sink_id="sk1")
        event = PipelineRegistered(pipeline=p)
        with pytest.raises(Exception):
            event.event_type = "changed"
