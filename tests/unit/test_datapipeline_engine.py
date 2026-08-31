from __future__ import annotations

import pytest

from eaip.datapipeline.engine import PipelineEngine
from eaip.datapipeline.exceptions import (
    PipelineExecutionError,
    PipelineNotFoundError,
    SinkNotFoundError,
    SourceNotFoundError,
)
from eaip.datapipeline.models import (
    DataSink,
    DataSource,
    ErrorHandlingMode,
    ExecutionStatus,
    Pipeline,
    PipelineConfig,
    PipelineExecution,
    PipelineStep,
    SinkType,
    SourceType,
    StepType,
    TriggerType,
)


@pytest.mark.asyncio
class TestSourceManagement:
    async def test_register_source(self) -> None:
        engine = PipelineEngine()
        source = DataSource(id="s1", name="src1", type=SourceType.API)
        await engine.register_source(source)
        result = await engine.get_source("s1")
        assert result.id == "s1"

    async def test_unregister_source(self) -> None:
        engine = PipelineEngine()
        source = DataSource(id="s1", name="src1", type=SourceType.API)
        await engine.register_source(source)
        await engine.unregister_source("s1")
        with pytest.raises(SourceNotFoundError):
            await engine.get_source("s1")

    async def test_unregister_source_not_found(self) -> None:
        engine = PipelineEngine()
        with pytest.raises(SourceNotFoundError):
            await engine.unregister_source("nonexistent")

    async def test_get_source_not_found(self) -> None:
        engine = PipelineEngine()
        with pytest.raises(SourceNotFoundError):
            await engine.get_source("nonexistent")


@pytest.mark.asyncio
class TestSinkManagement:
    async def test_register_sink(self) -> None:
        engine = PipelineEngine()
        sink = DataSink(id="sk1", name="sink1", type=SinkType.DATABASE)
        await engine.register_sink(sink)
        assert engine.config.max_records_per_run == 10000

    async def test_unregister_sink(self) -> None:
        engine = PipelineEngine()
        sink = DataSink(id="sk1", name="sink1", type=SinkType.FILE)
        await engine.register_sink(sink)
        await engine.unregister_sink("sk1")
        with pytest.raises(SinkNotFoundError):
            engine.get_sink("sk1")

    async def test_unregister_sink_not_found(self) -> None:
        engine = PipelineEngine()
        with pytest.raises(SinkNotFoundError):
            await engine.unregister_sink("nonexistent")


@pytest.mark.asyncio
class TestPipelineManagement:
    async def test_register_pipeline(self) -> None:
        engine = PipelineEngine()
        pipeline = Pipeline(id="p1", name="pipe1", source_id="s1", sink_id="sk1")
        await engine.register_pipeline(pipeline)
        assert engine.get_pipeline("p1").id == "p1"

    async def test_unregister_pipeline(self) -> None:
        engine = PipelineEngine()
        pipeline = Pipeline(id="p1", name="pipe1", source_id="s1", sink_id="sk1")
        await engine.register_pipeline(pipeline)
        await engine.unregister_pipeline("p1")
        with pytest.raises(PipelineNotFoundError):
            engine.get_pipeline("p1")

    async def test_list_pipelines_all(self) -> None:
        engine = PipelineEngine()
        await engine.register_pipeline(Pipeline(id="p1", name="a", source_id="s1", sink_id="sk1"))
        await engine.register_pipeline(Pipeline(id="p2", name="b", source_id="s2", sink_id="sk2"))
        assert len(engine.list_pipelines()) == 2

    async def test_list_pipelines_filter_source(self) -> None:
        engine = PipelineEngine()
        await engine.register_pipeline(Pipeline(id="p1", name="a", source_id="s1", sink_id="sk1"))
        await engine.register_pipeline(Pipeline(id="p2", name="b", source_id="s2", sink_id="sk1"))
        result = engine.list_pipelines(source_id="s1")
        assert len(result) == 1
        assert result[0].id == "p1"

    async def test_list_pipelines_filter_sink(self) -> None:
        engine = PipelineEngine()
        await engine.register_pipeline(Pipeline(id="p1", name="a", source_id="s1", sink_id="sk1"))
        await engine.register_pipeline(Pipeline(id="p2", name="b", source_id="s1", sink_id="sk2"))
        result = engine.list_pipelines(sink_id="sk2")
        assert len(result) == 1
        assert result[0].id == "p2"


class TestPipelineManagementSync:
    def test_get_pipeline_not_found(self) -> None:
        engine = PipelineEngine()
        with pytest.raises(PipelineNotFoundError):
            engine.get_pipeline("nonexistent")

    def test_list_pipelines_empty(self) -> None:
        engine = PipelineEngine()
        assert engine.list_pipelines() == []


@pytest.mark.asyncio
class TestPipelineExecution:
    @pytest.fixture
    async def engine_with_resources(self) -> PipelineEngine:
        engine = PipelineEngine()
        source = DataSource(
            id="s1",
            name="api-source",
            type=SourceType.API,
            config={"sample_data": [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]},
        )
        sink = DataSink(id="sk1", name="db-sink", type=SinkType.DATABASE)
        await engine.register_source(source)
        await engine.register_sink(sink)
        return engine

    async def test_execute_simple_pipeline(self, engine_with_resources: PipelineEngine) -> None:
        engine = engine_with_resources
        pipeline = Pipeline(id="p1", name="simple", source_id="s1", sink_id="sk1")
        await engine.register_pipeline(pipeline)
        execution = await engine.execute_pipeline("p1")
        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.records_read == 2
        assert execution.records_written == 2

    async def test_execute_pipeline_with_steps(self, engine_with_resources: PipelineEngine) -> None:
        engine = engine_with_resources
        step = PipelineStep(
            id="st1",
            name="upper",
            type=StepType.TRANSFORM,
            config={"mapping": {"name": "name", "id": "id"}},
        )
        pipeline = Pipeline(
            id="p2",
            name="with-steps",
            source_id="s1",
            sink_id="sk1",
            steps=(step,),
        )
        await engine.register_pipeline(pipeline)
        execution = await engine.execute_pipeline("p2")
        assert execution.status == ExecutionStatus.COMPLETED
        assert "st1" in execution.step_results

    async def test_execute_disabled_pipeline(self, engine_with_resources: PipelineEngine) -> None:
        engine = engine_with_resources
        pipeline = Pipeline(
            id="p3",
            name="disabled",
            source_id="s1",
            sink_id="sk1",
            enabled=False,
        )
        await engine.register_pipeline(pipeline)
        with pytest.raises(PipelineExecutionError, match="disabled"):
            await engine.execute_pipeline("p3")

    async def test_execute_pipeline_source_not_found(self) -> None:
        engine = PipelineEngine()
        pipeline = Pipeline(id="p1", name="x", source_id="missing", sink_id="sk1")
        await engine.register_pipeline(pipeline)
        await engine.register_sink(DataSink(id="sk1", name="s", type=SinkType.FILE))
        with pytest.raises(SourceNotFoundError):
            await engine.execute_pipeline("p1")

    async def test_execute_pipeline_sink_not_found(self) -> None:
        engine = PipelineEngine()
        pipeline = Pipeline(id="p1", name="x", source_id="s1", sink_id="missing")
        await engine.register_pipeline(pipeline)
        await engine.register_source(DataSource(id="s1", name="s", type=SourceType.API))
        with pytest.raises(SinkNotFoundError):
            await engine.execute_pipeline("p1")

    async def test_execute_pipeline_not_found(self) -> None:
        engine = PipelineEngine()
        with pytest.raises(PipelineNotFoundError):
            await engine.execute_pipeline("nonexistent")

    async def test_cancel_execution(self, engine_with_resources: PipelineEngine) -> None:
        engine = engine_with_resources
        pipeline = Pipeline(id="p1", name="simple", source_id="s1", sink_id="sk1")
        await engine.register_pipeline(pipeline)

        import uuid

        exec_ = PipelineExecution(
            id=str(uuid.uuid4()), pipeline_id="p1", status=ExecutionStatus.RUNNING
        )
        engine._executions[exec_.id] = exec_
        engine._active_executions.add(exec_.id)

        cancelled = await engine.cancel_execution(exec_.id)
        assert cancelled.status == ExecutionStatus.CANCELLED
        assert cancelled.error == "Cancelled by user"

    async def test_cancel_nonexistent_execution(self) -> None:
        engine = PipelineEngine()
        with pytest.raises(PipelineExecutionError):
            await engine.cancel_execution("nonexistent")

    async def test_get_execution(self, engine_with_resources: PipelineEngine) -> None:
        engine = engine_with_resources
        pipeline = Pipeline(id="p1", name="x", source_id="s1", sink_id="sk1")
        await engine.register_pipeline(pipeline)
        execution = await engine.execute_pipeline("p1")
        retrieved = await engine.get_execution(execution.id)
        assert retrieved.id == execution.id

    async def test_get_nonexistent_execution(self) -> None:
        engine = PipelineEngine()
        with pytest.raises(PipelineExecutionError):
            await engine.get_execution("nonexistent")

    async def test_list_executions_empty(self) -> None:
        engine = PipelineEngine()
        assert await engine.list_executions() == []

    async def test_list_executions_filter_pipeline(
        self,
        engine_with_resources: PipelineEngine,
    ) -> None:
        engine = engine_with_resources
        p1 = Pipeline(id="p1", name="a", source_id="s1", sink_id="sk1")
        p2 = Pipeline(id="p2", name="b", source_id="s1", sink_id="sk1")
        await engine.register_pipeline(p1)
        await engine.register_pipeline(p2)
        await engine.execute_pipeline("p1")
        await engine.execute_pipeline("p2")
        result = await engine.list_executions(pipeline_id="p1")
        assert all(e.pipeline_id == "p1" for e in result)

    async def test_list_executions_filter_status(
        self,
        engine_with_resources: PipelineEngine,
    ) -> None:
        engine = engine_with_resources
        p = Pipeline(id="p1", name="a", source_id="s1", sink_id="sk1")
        await engine.register_pipeline(p)
        await engine.execute_pipeline("p1")
        result = await engine.list_executions(status=ExecutionStatus.COMPLETED)
        assert len(result) >= 1

    async def test_execute_steps_abort_on_error(
        self,
        engine_with_resources: PipelineEngine,
    ) -> None:
        engine = engine_with_resources
        step = PipelineStep(
            id="bad",
            name="bad-step",
            type=StepType.VALIDATE,
            config={
                "rules": [
                    {"field": "missing", "type": "required"},
                ],
            },
        )
        pipeline = Pipeline(
            id="p1",
            name="abort-test",
            source_id="s1",
            sink_id="sk1",
            steps=(step,),
            error_handling=ErrorHandlingMode.ABORT,
        )
        await engine.register_pipeline(pipeline)
        execution = await engine.execute_pipeline("p1")
        assert execution.status == ExecutionStatus.FAILED

    async def test_register_and_execute_pipeline_trigger_scheduled(
        self,
        engine_with_resources: PipelineEngine,
    ) -> None:
        engine = engine_with_resources
        pipeline = Pipeline(id="p1", name="scheduled", source_id="s1", sink_id="sk1")
        await engine.register_pipeline(pipeline)
        execution = await engine.execute_pipeline("p1", trigger_type=TriggerType.SCHEDULED)
        assert execution.trigger_type == TriggerType.SCHEDULED

    async def test_concurrent_execution_limit(self) -> None:
        config = PipelineConfig()
        engine = PipelineEngine(config=config)
        source = DataSource(id="s1", name="src", type=SourceType.API)
        sink = DataSink(id="sk1", name="sk", type=SinkType.FILE)
        await engine.register_source(source)
        await engine.register_sink(sink)
        pipeline = Pipeline(id="p1", name="conc", source_id="s1", sink_id="sk1")
        await engine.register_pipeline(pipeline)
        assert engine._semaphore._value == 10
