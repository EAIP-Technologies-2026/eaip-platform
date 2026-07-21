from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.datapipeline.models import (
    DataRecord,
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


class TestDataSource:
    def test_basic_source(self) -> None:
        source = DataSource(id="src1", name="Test Source", type=SourceType.API)
        assert source.id == "src1"
        assert source.name == "Test Source"
        assert source.type == SourceType.API
        assert source.enabled is True
        assert source.max_retries == 3
        assert source.timeout_seconds == 30.0

    def test_source_with_all_fields(self) -> None:
        source = DataSource(
            id="src2",
            name="Full Source",
            type=SourceType.DATABASE,
            config={"host": "localhost", "port": 5432},
            credentials_ref="vault://db-creds",
            data_schema={"type": "object"},
            enabled=False,
            tags=("db", "production"),
            metadata={"owner": "team-a"},
            max_retries=5,
            timeout_seconds=60.0,
        )
        assert source.config["host"] == "localhost"
        assert source.credentials_ref == "vault://db-creds"
        assert source.enabled is False
        assert "db" in source.tags

    def test_source_frozen(self) -> None:
        source = DataSource(id="src1", name="Test", type=SourceType.FILE)
        with pytest.raises(ValidationError):
            source.id = "changed"

    def test_source_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            DataSource(id="s1", name="x", type=SourceType.HTTP, unknown_field="x")


class TestDataSink:
    def test_basic_sink(self) -> None:
        sink = DataSink(id="sink1", name="Test Sink", type=SinkType.DATABASE)
        assert sink.id == "sink1"
        assert sink.enabled is True

    def test_sink_frozen(self) -> None:
        sink = DataSink(id="s1", name="x", type=SinkType.FILE)
        with pytest.raises(ValidationError):
            sink.name = "changed"


class TestPipelineStep:
    def test_basic_step(self) -> None:
        step = PipelineStep(id="step1", name="Transform Step", type=StepType.TRANSFORM)
        assert step.id == "step1"
        assert step.type == StepType.TRANSFORM
        assert step.enabled is True

    def test_step_with_config(self) -> None:
        step = PipelineStep(
            id="step2",
            name="Filter",
            type=StepType.FILTER,
            config={"condition": {"field": "age", "operator": "gt", "value": 18}},
            retry_policy={"max_retries": 3, "delay_seconds": 1.0},
        )
        assert step.config["condition"]["field"] == "age"
        assert step.retry_policy["max_retries"] == 3


class TestPipeline:
    def test_basic_pipeline(self) -> None:
        pipeline = Pipeline(
            id="pipe1",
            name="ETL Pipeline",
            source_id="src1",
            sink_id="sink1",
        )
        assert pipeline.id == "pipe1"
        assert pipeline.source_id == "src1"
        assert pipeline.error_handling == ErrorHandlingMode.ABORT
        assert pipeline.max_concurrent == 1
        assert pipeline.enabled is True

    def test_pipeline_with_steps(self) -> None:
        step = PipelineStep(id="s1", name="Transform", type=StepType.TRANSFORM)
        pipeline = Pipeline(
            id="pipe2",
            name="With Steps",
            source_id="src1",
            sink_id="sink1",
            steps=(step,),
            schedule_cron="0 */6 * * *",
            error_handling=ErrorHandlingMode.SKIP,
        )
        assert len(pipeline.steps) == 1
        assert pipeline.schedule_cron == "0 */6 * * *"
        assert pipeline.error_handling == ErrorHandlingMode.SKIP

    def test_pipeline_frozen(self) -> None:
        pipeline = Pipeline(id="p1", name="x", source_id="s1", sink_id="sk1")
        with pytest.raises(ValidationError):
            pipeline.name = "y"


class TestPipelineExecution:
    def test_basic_execution(self) -> None:
        exec_ = PipelineExecution(id="exec1", pipeline_id="pipe1")
        assert exec_.status == ExecutionStatus.PENDING
        assert exec_.trigger_type == TriggerType.MANUAL
        assert exec_.records_read == 0

    def test_completed_execution(self) -> None:
        import datetime

        now = datetime.datetime.now(datetime.UTC)
        exec_ = PipelineExecution(
            id="exec2",
            pipeline_id="pipe1",
            status=ExecutionStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            duration_ms=1500.0,
            records_read=100,
            records_written=95,
            records_failed=5,
            trigger_type=TriggerType.SCHEDULED,
        )
        assert exec_.status == ExecutionStatus.COMPLETED
        assert exec_.records_read == 100
        assert exec_.trigger_type == TriggerType.SCHEDULED


class TestDataRecord:
    def test_basic_record(self) -> None:
        record = DataRecord(id="rec1", data={"name": "test"}, source="src1")
        assert record.data["name"] == "test"
        assert record.schema_version == ""

    def test_record_with_metadata(self) -> None:
        record = DataRecord(
            id="rec2",
            data={"value": 42},
            metadata={"origin": "api"},
            source="src2",
            schema_version="1.0",
            checksum="abc123",
        )
        assert record.metadata["origin"] == "api"
        assert record.checksum == "abc123"


class TestPipelineConfig:
    def test_default_config(self) -> None:
        config = PipelineConfig()
        assert config.max_records_per_run == 10000
        assert config.default_batch_size == 100
        assert config.enable_lineage_tracking is True
        assert config.retention_days == 30
        assert config.max_execution_history == 1000

    def test_custom_config(self) -> None:
        config = PipelineConfig(
            max_records_per_run=5000,
            default_batch_size=50,
            enable_lineage_tracking=False,
            retention_days=7,
            max_execution_history=100,
        )
        assert config.max_records_per_run == 5000
        assert config.enable_lineage_tracking is False


class TestEnums:
    def test_source_type_values(self) -> None:
        assert SourceType.HTTP.value == "http"
        assert SourceType.API.value == "api"
        assert SourceType.QUEUE.value == "queue"

    def test_step_type_values(self) -> None:
        assert StepType.TRANSFORM.value == "transform"
        assert StepType.AGGREGATE.value == "aggregate"
        assert StepType.SCRIPT.value == "script"

    def test_execution_status_values(self) -> None:
        assert ExecutionStatus.PENDING.value == "pending"
        assert ExecutionStatus.CANCELLED.value == "cancelled"

    def test_trigger_type_values(self) -> None:
        assert TriggerType.MANUAL.value == "manual"
        assert TriggerType.EVENT.value == "event"

    def test_error_handling_values(self) -> None:
        assert ErrorHandlingMode.ABORT.value == "abort"
        assert ErrorHandlingMode.ISOLATION.value == "isolation"
