"""PipelineOrchestrator — create, run, and manage pipelines and stages."""

from __future__ import annotations

import asyncio
from typing import Any

from eaip.logging.context import get_logger
from eaip.porch.events import (
    PipelineCompleted,
    PipelineCreated,
    PipelineFailed,
    PipelineStarted,
    StageCompleted,
    StageFailed,
    StageStarted,
)
from eaip.porch.exceptions import (
    OrchestratorError,
    PipelineNotFoundError,
    StageExecutionError,
)
from eaip.porch.models import (
    OrchestratorConfig,
    Pipeline,
    PipelineRun,
    Stage,
    StageStatus,
)
from eaip.shared.time import utc_now


class PipelineOrchestrator:
    def __init__(self, config: OrchestratorConfig | None = None) -> None:
        self._config = config or OrchestratorConfig()
        self._pipelines: dict[str, Pipeline] = {}
        self._runs: dict[str, PipelineRun] = {}
        self._run_counter: int = 0
        self._log = get_logger("eaip.porch.orchestrator")

    @property
    def config(self) -> OrchestratorConfig:
        return self._config

    async def create_pipeline(
        self,
        pipeline: Pipeline,
    ) -> Pipeline:
        self._pipelines[pipeline.id] = pipeline
        PipelineCreated(pipeline_id=pipeline.id, name=pipeline.name)
        self._log.info("porch.pipeline.created", id=pipeline.id, name=pipeline.name)
        return pipeline

    async def get_pipeline(self, pipeline_id: str) -> Pipeline:
        pipe = self._pipelines.get(pipeline_id)
        if pipe is None:
            raise PipelineNotFoundError(f"Pipeline '{pipeline_id}' not found")
        return pipe

    async def list_pipelines(self) -> list[Pipeline]:
        return list(self._pipelines.values())

    async def update_pipeline(
        self,
        pipeline_id: str,
        **updates: Any,
    ) -> Pipeline:
        pipe = await self.get_pipeline(pipeline_id)
        pipe = pipe.model_copy(update=updates, deep=True)
        self._pipelines[pipeline_id] = pipe
        self._log.info("porch.pipeline.updated", id=pipeline_id)
        return pipe

    async def delete_pipeline(self, pipeline_id: str) -> None:
        if pipeline_id not in self._pipelines:
            raise PipelineNotFoundError(f"Pipeline '{pipeline_id}' not found")
        del self._pipelines[pipeline_id]
        self._log.info("porch.pipeline.deleted", id=pipeline_id)

    async def run_pipeline(
        self,
        pipeline_id: str,
    ) -> PipelineRun:
        pipe = await self.get_pipeline(pipeline_id)
        self._run_counter += 1
        run_id = f"run_{self._run_counter}"

        run_stages = tuple(
            Stage(
                id=s.id,
                pipeline_id=s.pipeline_id,
                name=s.name,
                order=s.order,
                depends_on=s.depends_on,
                timeout_seconds=s.timeout_seconds,
                retry_count=s.retry_count,
                status=StageStatus.PENDING,
            )
            for s in pipe.stages
        )

        run = PipelineRun(
            id=run_id,
            pipeline_id=pipeline_id,
            status="running",
            stages=run_stages,
        )
        self._runs[run_id] = run
        PipelineStarted(pipeline_id=pipeline_id, run_id=run_id)
        self._log.info("porch.pipeline.started", pipeline_id=pipeline_id, run_id=run_id)

        try:
            await self._execute_stages(run_id)
            run = self._runs[run_id]
            run = run.model_copy(
                update={"status": "completed", "completed_at": utc_now()},
                deep=True,
            )
            self._runs[run_id] = run
            PipelineCompleted(pipeline_id=pipeline_id, run_id=run_id)
            self._log.info("porch.pipeline.completed", run_id=run_id)
        except Exception as exc:
            run = self._runs[run_id]
            run = run.model_copy(
                update={
                    "status": "failed",
                    "completed_at": utc_now(),
                    "error_message": str(exc),
                },
                deep=True,
            )
            self._runs[run_id] = run
            PipelineFailed(pipeline_id=pipeline_id, run_id=run_id, error=str(exc))
            self._log.error("porch.pipeline.failed", run_id=run_id, error=str(exc))

        return self._runs[run_id]

    async def _execute_stages(self, run_id: str) -> None:
        run = self._runs[run_id]
        completed: set[str] = set()
        failed: set[str] = set()

        def _deps_met(stage: Stage) -> bool:
            return all(d in completed for d in stage.depends_on)

        while len(completed) + len(failed) < len(run.stages):
            ready = [
                s
                for s in run.stages
                if s.status == StageStatus.PENDING and _deps_met(s) and s.id not in failed
            ]
            if not ready:
                pending = [s for s in run.stages if s.status == StageStatus.PENDING]
                if pending and not any(_deps_met(s) for s in pending):
                    raise StageExecutionError(
                        "Circular or unsatisfiable stage dependencies detected"
                    )
                if not pending:
                    break
                await asyncio.sleep(0.01)
                continue

            for stage in ready:
                stage_idx = next(i for i, s in enumerate(run.stages) if s.id == stage.id)
                updated_stage = stage.model_copy(
                    update={"status": StageStatus.RUNNING, "started_at": utc_now()},
                    deep=True,
                )
                stages_list = list(run.stages)
                stages_list[stage_idx] = updated_stage
                run = run.model_copy(update={"stages": tuple(stages_list)}, deep=True)
                self._runs[run.id] = run

                StageStarted(
                    pipeline_id=run.pipeline_id,
                    run_id=run.id,
                    stage_id=stage.id,
                    stage_name=stage.name,
                )

                try:
                    await asyncio.sleep(0.05)
                    stages_list = list(run.stages)
                    stages_list[stage_idx] = updated_stage.model_copy(
                        update={
                            "status": StageStatus.COMPLETED,
                            "completed_at": utc_now(),
                        },
                        deep=True,
                    )
                    run = run.model_copy(update={"stages": tuple(stages_list)}, deep=True)
                    self._runs[run.id] = run
                    completed.add(stage.id)
                    StageCompleted(
                        pipeline_id=run.pipeline_id,
                        run_id=run.id,
                        stage_id=stage.id,
                        stage_name=stage.name,
                    )
                    self._log.info(
                        "porch.stage.completed",
                        stage_id=stage.id,
                        run_id=run.id,
                    )
                except Exception as exc:
                    stages_list = list(run.stages)
                    stages_list[stage_idx] = updated_stage.model_copy(
                        update={
                            "status": StageStatus.FAILED,
                            "completed_at": utc_now(),
                        },
                        deep=True,
                    )
                    run = run.model_copy(update={"stages": tuple(stages_list)}, deep=True)
                    self._runs[run.id] = run
                    failed.add(stage.id)
                    StageFailed(
                        pipeline_id=run.pipeline_id,
                        run_id=run.id,
                        stage_id=stage.id,
                        stage_name=stage.name,
                        error=str(exc),
                    )
                    self._log.error(
                        "porch.stage.failed",
                        stage_id=stage.id,
                        run_id=run.id,
                        error=str(exc),
                    )
                    raise

    async def get_run(self, run_id: str) -> PipelineRun:
        run = self._runs.get(run_id)
        if run is None:
            raise PipelineNotFoundError(f"Run '{run_id}' not found")
        return run

    async def get_stage(self, run_id: str, stage_id: str) -> Stage:
        run = await self.get_run(run_id)
        for stage in run.stages:
            if stage.id == stage_id:
                return stage
        raise StageExecutionError(f"Stage '{stage_id}' not found in run '{run_id}'")

    async def retry_stage(self, run_id: str, stage_id: str) -> Stage:
        run = await self.get_run(run_id)
        stage = await self.get_stage(run_id, stage_id)
        if stage.status != StageStatus.FAILED:
            raise StageExecutionError(
                f"Stage '{stage_id}' is not in FAILED state (current: {stage.status})"
            )
        stage_idx = next(i for i, s in enumerate(run.stages) if s.id == stage_id)
        updated_stage = stage.model_copy(
            update={
                "status": StageStatus.PENDING,
                "started_at": None,
                "completed_at": None,
            },
            deep=True,
        )
        stages_list = list(run.stages)
        stages_list[stage_idx] = updated_stage
        run = run.model_copy(update={"stages": tuple(stages_list)}, deep=True)
        self._runs[run_id] = run
        self._log.info("porch.stage.retried", stage_id=stage_id, run_id=run_id)
        return updated_stage

    async def skip_stage(self, run_id: str, stage_id: str) -> Stage:
        run = await self.get_run(run_id)
        stage = await self.get_stage(run_id, stage_id)
        if stage.status != StageStatus.PENDING:
            raise StageExecutionError(
                f"Stage '{stage_id}' is not in PENDING state (current: {stage.status})"
            )
        stage_idx = next(i for i, s in enumerate(run.stages) if s.id == stage_id)
        updated_stage = stage.model_copy(
            update={"status": StageStatus.SKIPPED, "completed_at": utc_now()},
            deep=True,
        )
        stages_list = list(run.stages)
        stages_list[stage_idx] = updated_stage
        run = run.model_copy(update={"stages": tuple(stages_list)}, deep=True)
        self._runs[run_id] = run
        self._log.info("porch.stage.skipped", stage_id=stage_id, run_id=run_id)
        return updated_stage

    async def cancel_run(self, run_id: str) -> PipelineRun:
        run = await self.get_run(run_id)
        if run.status not in ("running", "pending"):
            raise OrchestratorError(f"Run '{run_id}' cannot be cancelled (status: {run.status})")
        stages_list = list(run.stages)
        for i, stage in enumerate(stages_list):
            if stage.status == StageStatus.PENDING:
                stages_list[i] = stage.model_copy(
                    update={"status": StageStatus.SKIPPED},
                    deep=True,
                )
        run = run.model_copy(
            update={
                "status": "cancelled",
                "completed_at": utc_now(),
                "stages": tuple(stages_list),
            },
            deep=True,
        )
        self._runs[run_id] = run
        self._log.info("porch.run.cancelled", run_id=run_id)
        return run


__all__ = ["PipelineOrchestrator"]
