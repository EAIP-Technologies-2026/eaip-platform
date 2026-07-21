from __future__ import annotations

import asyncio
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from eaip.datapipeline.events import (
    PipelineExecutionCompleted,
    PipelineExecutionFailed,
    PipelineExecutionStarted,
    PipelineRegistered,
    PipelineStepCompleted,
    PipelineStepFailed,
    PipelineUnregistered,
    SinkRegistered,
    SinkUnregistered,
    SourceRegistered,
    SourceUnregistered,
)
from eaip.datapipeline.exceptions import (
    PipelineExecutionError,
    PipelineNotFoundError,
    SinkNotFoundError,
    SourceNotFoundError,
)
from eaip.datapipeline.lineage import DataLineageTracker
from eaip.datapipeline.models import (
    DataRecord,
    DataSink,
    DataSource,
    ErrorHandlingMode,
    ExecutionStatus,
    Pipeline,
    PipelineConfig,
    PipelineExecution,
    TriggerType,
)
from eaip.datapipeline.scheduler import PipelineScheduler
from eaip.datapipeline.steps import StepExecutor
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger


class PipelineEngine:
    def __init__(
        self,
        config: PipelineConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config = config or PipelineConfig()
        self._event_bus = event_bus or EventBus()
        self._log = get_logger("eaip.datapipeline.engine")
        self._sources: dict[str, DataSource] = {}
        self._sinks: dict[str, DataSink] = {}
        self._pipelines: dict[str, Pipeline] = {}
        self._executions: dict[str, PipelineExecution] = {}
        self._active_executions: set[str] = set()
        self._step_executor = StepExecutor()
        self._scheduler = PipelineScheduler()
        self._lineage = DataLineageTracker()
        self._semaphore = asyncio.Semaphore(10)

    @property
    def config(self) -> PipelineConfig:
        return self._config

    async def register_source(self, source: DataSource) -> None:
        self._sources[source.id] = source
        await self._event_bus.publish(SourceRegistered(source=source))
        self._log.info("source.registered", source_id=source.id, source_name=source.name)

    async def unregister_source(self, source_id: str) -> None:
        source = self._sources.pop(source_id, None)
        if source is None:
            raise SourceNotFoundError(
                f"Source {source_id!r} not found",
                context={"source_id": source_id},
            )
        await self._event_bus.publish(
            SourceUnregistered(source_id=source_id, source_name=source.name),
        )
        self._log.info("source.unregistered", source_id=source_id)

    async def get_source(self, source_id: str) -> DataSource:
        source = self._sources.get(source_id)
        if source is None:
            raise SourceNotFoundError(
                f"Source {source_id!r} not found",
                context={"source_id": source_id},
            )
        return source

    async def register_sink(self, sink: DataSink) -> None:
        self._sinks[sink.id] = sink
        await self._event_bus.publish(SinkRegistered(sink=sink))
        self._log.info("sink.registered", sink_id=sink.id, sink_name=sink.name)

    async def unregister_sink(self, sink_id: str) -> None:
        sink = self._sinks.pop(sink_id, None)
        if sink is None:
            raise SinkNotFoundError(
                f"Sink {sink_id!r} not found",
                context={"sink_id": sink_id},
            )
        await self._event_bus.publish(
            SinkUnregistered(sink_id=sink_id, sink_name=sink.name),
        )
        self._log.info("sink.unregistered", sink_id=sink_id)

    def get_sink(self, sink_id: str) -> DataSink:
        sink = self._sinks.get(sink_id)
        if sink is None:
            raise SinkNotFoundError(
                f"Sink {sink_id!r} not found",
                context={"sink_id": sink_id},
            )
        return sink

    async def register_pipeline(self, pipeline: Pipeline) -> None:
        self._pipelines[pipeline.id] = pipeline
        await self._event_bus.publish(PipelineRegistered(pipeline=pipeline))
        self._log.info(
            "pipeline.registered",
            pipeline_id=pipeline.id,
            pipeline_name=pipeline.name,
        )

    async def unregister_pipeline(self, pipeline_id: str) -> None:
        pipeline = self._pipelines.pop(pipeline_id, None)
        if pipeline is None:
            raise PipelineNotFoundError(
                f"Pipeline {pipeline_id!r} not found",
                context={"pipeline_id": pipeline_id},
            )
        await self._event_bus.publish(
            PipelineUnregistered(pipeline_id=pipeline_id, pipeline_name=pipeline.name),
        )
        self._log.info("pipeline.unregistered", pipeline_id=pipeline_id)

    def get_pipeline(self, pipeline_id: str) -> Pipeline:
        pipeline = self._pipelines.get(pipeline_id)
        if pipeline is None:
            raise PipelineNotFoundError(
                f"Pipeline {pipeline_id!r} not found",
                context={"pipeline_id": pipeline_id},
            )
        return pipeline

    def list_pipelines(
        self,
        source_id: str | None = None,
        sink_id: str | None = None,
    ) -> list[Pipeline]:
        result = list(self._pipelines.values())
        if source_id is not None:
            result = [p for p in result if p.source_id == source_id]
        if sink_id is not None:
            result = [p for p in result if p.sink_id == sink_id]
        return result

    async def execute_pipeline(
        self,
        pipeline_id: str,
        trigger_type: TriggerType = TriggerType.MANUAL,
    ) -> PipelineExecution:
        pipeline = self.get_pipeline(pipeline_id)

        if not pipeline.enabled:
            raise PipelineExecutionError(
                f"Pipeline {pipeline_id!r} is disabled",
                context={"pipeline_id": pipeline_id},
            )

        source = await self.get_source(pipeline.source_id)
        if not source.enabled:
            raise PipelineExecutionError(
                f"Source {source.id!r} is disabled",
                context={"source_id": source.id, "pipeline_id": pipeline_id},
            )

        sink = self.get_sink(pipeline.sink_id)
        if not sink.enabled:
            raise PipelineExecutionError(
                f"Sink {sink.id!r} is disabled",
                context={"sink_id": sink.id, "pipeline_id": pipeline_id},
            )

        execution_id = str(uuid.uuid4())
        execution = PipelineExecution(
            id=execution_id,
            pipeline_id=pipeline.id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(UTC),
            trigger_type=trigger_type,
        )
        self._executions[execution_id] = execution
        self._active_executions.add(execution_id)

        await self._event_bus.publish(
            PipelineExecutionStarted(execution=execution),
        )

        async with self._semaphore:
            try:
                context: dict[str, Any] = {
                    "pipeline": pipeline,
                    "source": source,
                    "sink": sink,
                    "execution_id": execution_id,
                }

                records = await self._read_source(source, context)
                execution = execution.model_copy(
                    update={"records_read": len(records)},
                )

                processed_records = await self.execute_steps(pipeline, execution, context, records)

                write_count = await self._write_sink(sink, processed_records, context)

                updated_execution = self._executions.get(execution_id)
                step_results = (
                    updated_execution.step_results if updated_execution else execution.step_results
                )

                if self._config.enable_lineage_tracking:
                    for record in processed_records:
                        await self._lineage.record_lineage(
                            execution_id=execution_id,
                            source=pipeline.source_id,
                            record_id=record.id,
                            step_id="sink",
                            target=pipeline.sink_id,
                        )

                started_dt = execution.started_at or datetime.now(UTC)
                duration_ms = (datetime.now(UTC) - started_dt).total_seconds() * 1000
                execution = PipelineExecution(
                    id=execution_id,
                    pipeline_id=pipeline.id,
                    status=ExecutionStatus.COMPLETED,
                    started_at=execution.started_at,
                    completed_at=datetime.now(UTC),
                    duration_ms=duration_ms,
                    records_read=len(records),
                    records_written=write_count,
                    records_failed=0,
                    step_results=step_results,
                    trigger_type=trigger_type,
                )
                self._executions[execution_id] = execution

                await self._event_bus.publish(
                    PipelineExecutionCompleted(execution=execution),
                )
                self._log.info(
                    "pipeline.execution.completed",
                    pipeline_id=pipeline_id,
                    execution_id=execution_id,
                    records_read=len(records),
                    records_written=write_count,
                )

            except Exception as exc:
                started_dt = execution.started_at or datetime.now(UTC)
                duration_ms = (datetime.now(UTC) - started_dt).total_seconds() * 1000
                execution = PipelineExecution(
                    id=execution_id,
                    pipeline_id=pipeline.id,
                    status=ExecutionStatus.FAILED,
                    started_at=execution.started_at,
                    completed_at=datetime.now(UTC),
                    duration_ms=duration_ms,
                    records_read=execution.records_read,
                    records_written=execution.records_written,
                    records_failed=0,
                    error=str(exc),
                    step_results=execution.step_results,
                    trigger_type=trigger_type,
                )
                self._executions[execution_id] = execution

                await self._event_bus.publish(
                    PipelineExecutionFailed(execution=execution, error=str(exc)),
                )
                self._log.error(
                    "pipeline.execution.failed",
                    pipeline_id=pipeline_id,
                    execution_id=execution_id,
                    error=str(exc),
                )

            finally:
                self._active_executions.discard(execution_id)

        return execution

    async def execute_steps(
        self,
        pipeline: Pipeline,
        execution: PipelineExecution,
        context: dict[str, Any],
        records: list[DataRecord] | None = None,
    ) -> list[DataRecord]:
        if records is None:
            records = await self._read_source(await self.get_source(pipeline.source_id), context)

        if not pipeline.steps:
            return records

        step_results: dict[str, Any] = {}

        for step in pipeline.steps:
            processed: list[DataRecord] = []
            step_start = time.monotonic()

            if step.type.value == "aggregate":
                try:
                    aggregated = await self._step_executor.execute_aggregate(
                        step,
                        records,
                        context,
                    )
                    processed = aggregated
                except Exception as exc:
                    await self._event_bus.publish(
                        PipelineStepFailed(
                            execution_id=execution.id,
                            step=step,
                            error=str(exc),
                            attempt=1,
                        ),
                    )
                    if pipeline.error_handling == ErrorHandlingMode.ABORT:
                        raise
                    if pipeline.error_handling == ErrorHandlingMode.SKIP:
                        processed = records
                    elif pipeline.error_handling == ErrorHandlingMode.ISOLATION:
                        processed = []
                else:
                    await self._event_bus.publish(
                        PipelineStepCompleted(
                            execution_id=execution.id,
                            step=step,
                            records_processed=len(processed),
                            duration_ms=(time.monotonic() - step_start) * 1000,
                        ),
                    )

                step_results[step.id] = {
                    "records_in": len(records),
                    "records_out": len(processed),
                    "duration_ms": (time.monotonic() - step_start) * 1000,
                }
                records = processed
                continue

            for record in records:
                try:
                    result = await self._step_executor.run_step(step, record, context)
                    if result is not None:
                        processed.append(result)
                except Exception as exc:
                    await self._event_bus.publish(
                        PipelineStepFailed(
                            execution_id=execution.id,
                            step=step,
                            error=str(exc),
                            attempt=1,
                        ),
                    )
                    if pipeline.error_handling == ErrorHandlingMode.ABORT:
                        raise
                    if pipeline.error_handling == ErrorHandlingMode.ISOLATION:
                        continue
                    if pipeline.error_handling == ErrorHandlingMode.SKIP:
                        processed.append(record)

            await self._event_bus.publish(
                PipelineStepCompleted(
                    execution_id=execution.id,
                    step=step,
                    records_processed=len(processed),
                    duration_ms=(time.monotonic() - step_start) * 1000,
                ),
            )

            step_results[step.id] = {
                "records_in": len(records),
                "records_out": len(processed),
                "duration_ms": (time.monotonic() - step_start) * 1000,
            }

            if self._config.enable_lineage_tracking:
                for rec in processed:
                    await self._lineage.record_lineage(
                        execution_id=execution.id,
                        source=pipeline.source_id,
                        record_id=rec.id,
                        step_id=step.id,
                        target=step.id,
                    )

            records = processed

        self._executions[execution.id] = execution.model_copy(
            update={"step_results": step_results},
        )
        return records

    async def cancel_execution(self, execution_id: str) -> PipelineExecution:
        execution = self._executions.get(execution_id)
        if execution is None:
            raise PipelineExecutionError(
                f"Execution {execution_id!r} not found",
                context={"execution_id": execution_id},
            )
        if execution.status not in (ExecutionStatus.PENDING, ExecutionStatus.RUNNING):
            return execution

        execution = PipelineExecution(
            id=execution.id,
            pipeline_id=execution.pipeline_id,
            status=ExecutionStatus.CANCELLED,
            started_at=execution.started_at,
            completed_at=datetime.now(UTC),
            duration_ms=(
                (datetime.now(UTC) - execution.started_at).total_seconds() * 1000
                if execution.started_at
                else 0.0
            ),
            records_read=execution.records_read,
            records_written=execution.records_written,
            records_failed=execution.records_failed,
            error="Cancelled by user",
            step_results=execution.step_results,
            trigger_type=execution.trigger_type,
        )
        self._executions[execution_id] = execution
        self._active_executions.discard(execution_id)
        return execution

    async def get_execution(self, execution_id: str) -> PipelineExecution:
        execution = self._executions.get(execution_id)
        if execution is None:
            raise PipelineExecutionError(
                f"Execution {execution_id!r} not found",
                context={"execution_id": execution_id},
            )
        return execution

    async def list_executions(
        self,
        pipeline_id: str | None = None,
        status: ExecutionStatus | None = None,
        limit: int = 100,
    ) -> list[PipelineExecution]:
        result = list(self._executions.values())
        if pipeline_id is not None:
            result = [e for e in result if e.pipeline_id == pipeline_id]
        if status is not None:
            result = [e for e in result if e.status == status]
        result.sort(key=lambda e: e.started_at or datetime.min, reverse=True)
        return result[:limit]

    async def _read_source(
        self,
        source: DataSource,
        context: dict[str, Any],
    ) -> list[DataRecord]:
        sample_data = source.config.get("sample_data", [])
        if sample_data:
            return [
                DataRecord(
                    id=str(uuid.uuid4()),
                    data=item if isinstance(item, dict) else {"value": item},
                    source=source.id,
                )
                for item in sample_data
            ]
        return [
            DataRecord(
                id=str(uuid.uuid4()),
                data={},
                source=source.id,
            ),
        ]

    async def _write_sink(
        self,
        sink: DataSink,
        records: list[DataRecord],
        context: dict[str, Any],
    ) -> int:
        return len(records)

    @property
    def scheduler(self) -> PipelineScheduler:
        return self._scheduler

    @property
    def lineage(self) -> DataLineageTracker:
        return self._lineage


__all__ = ["PipelineEngine"]
