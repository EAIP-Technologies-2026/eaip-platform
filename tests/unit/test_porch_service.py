"""Tests for PipelineOrchestrator."""

from __future__ import annotations

import pytest

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
from eaip.porch.orchestrator import PipelineOrchestrator


class TestPipelineOrchestrator:
    @pytest.fixture
    def orchestrator(self) -> PipelineOrchestrator:
        return PipelineOrchestrator()

    @pytest.fixture
    def sample_stage(self) -> Stage:
        return Stage(id="st1", pipeline_id="p1", name="Build", order=0)

    @pytest.fixture
    def sample_pipeline(self, sample_stage: Stage) -> Pipeline:
        return Pipeline(id="p1", name="CI Pipeline", stages=(sample_stage,))

    class TestCreatePipeline:
        async def test_create(
            self, orchestrator: PipelineOrchestrator, sample_pipeline: Pipeline
        ) -> None:
            result = await orchestrator.create_pipeline(sample_pipeline)
            assert result.id == "p1"
            assert result.name == "CI Pipeline"

        async def test_list(
            self, orchestrator: PipelineOrchestrator, sample_pipeline: Pipeline
        ) -> None:
            await orchestrator.create_pipeline(sample_pipeline)
            pipelines = await orchestrator.list_pipelines()
            assert len(pipelines) == 1

    class TestGetPipeline:
        async def test_get(
            self, orchestrator: PipelineOrchestrator, sample_pipeline: Pipeline
        ) -> None:
            await orchestrator.create_pipeline(sample_pipeline)
            pipe = await orchestrator.get_pipeline("p1")
            assert pipe.name == "CI Pipeline"

        async def test_not_found(self, orchestrator: PipelineOrchestrator) -> None:
            with pytest.raises(PipelineNotFoundError):
                await orchestrator.get_pipeline("nonexistent")

    class TestUpdatePipeline:
        async def test_update(
            self, orchestrator: PipelineOrchestrator, sample_pipeline: Pipeline
        ) -> None:
            await orchestrator.create_pipeline(sample_pipeline)
            updated = await orchestrator.update_pipeline("p1", name="Updated Pipeline")
            assert updated.name == "Updated Pipeline"

    class TestDeletePipeline:
        async def test_delete(
            self, orchestrator: PipelineOrchestrator, sample_pipeline: Pipeline
        ) -> None:
            await orchestrator.create_pipeline(sample_pipeline)
            await orchestrator.delete_pipeline("p1")
            with pytest.raises(PipelineNotFoundError):
                await orchestrator.get_pipeline("p1")

    class TestRunPipeline:
        async def test_run_success(
            self, orchestrator: PipelineOrchestrator, sample_pipeline: Pipeline
        ) -> None:
            await orchestrator.create_pipeline(sample_pipeline)
            run = await orchestrator.run_pipeline("p1")
            assert run.status == "completed"
            assert len(run.stages) == 1

        async def test_run_not_found(self, orchestrator: PipelineOrchestrator) -> None:
            with pytest.raises(PipelineNotFoundError):
                await orchestrator.run_pipeline("nonexistent")

        async def test_run_with_dependencies(self, orchestrator: PipelineOrchestrator) -> None:
            st1 = Stage(id="st1", pipeline_id="p1", name="Build", order=0)
            st2 = Stage(id="st2", pipeline_id="p1", name="Test", order=1, depends_on=("st1",))
            pipe = Pipeline(id="p1", name="Pipeline", stages=(st1, st2))
            await orchestrator.create_pipeline(pipe)
            run = await orchestrator.run_pipeline("p1")
            assert run.status == "completed"
            assert all(s.status == StageStatus.COMPLETED for s in run.stages)

    class TestGetRun:
        async def test_get_run(
            self, orchestrator: PipelineOrchestrator, sample_pipeline: Pipeline
        ) -> None:
            await orchestrator.create_pipeline(sample_pipeline)
            run = await orchestrator.run_pipeline("p1")
            fetched = await orchestrator.get_run(run.id)
            assert fetched.id == run.id

        async def test_get_run_not_found(self, orchestrator: PipelineOrchestrator) -> None:
            with pytest.raises(PipelineNotFoundError):
                await orchestrator.get_run("nonexistent")

    class TestGetStage:
        async def test_get_stage(
            self, orchestrator: PipelineOrchestrator, sample_pipeline: Pipeline
        ) -> None:
            await orchestrator.create_pipeline(sample_pipeline)
            run = await orchestrator.run_pipeline("p1")
            stage = await orchestrator.get_stage(run.id, "st1")
            assert stage.id == "st1"

        async def test_get_stage_not_found(
            self, orchestrator: PipelineOrchestrator, sample_pipeline: Pipeline
        ) -> None:
            await orchestrator.create_pipeline(sample_pipeline)
            run = await orchestrator.run_pipeline("p1")
            with pytest.raises(StageExecutionError):
                await orchestrator.get_stage(run.id, "nonexistent")

    class TestRetryStage:
        async def test_retry(self, orchestrator: PipelineOrchestrator) -> None:
            st1 = Stage(id="st1", pipeline_id="p1", name="Build", order=0)
            pipe = Pipeline(id="p1", name="Pipeline", stages=(st1,))
            await orchestrator.create_pipeline(pipe)
            run = await orchestrator.run_pipeline("p1")
            run = await orchestrator.get_run(run.id)
            stage = await orchestrator.get_stage(run.id, "st1")
            assert stage.status == StageStatus.COMPLETED

    class TestSkipStage:
        async def test_skip(self, orchestrator: PipelineOrchestrator) -> None:
            st1 = Stage(
                id="st1", pipeline_id="p1", name="Build", order=0, status=StageStatus.PENDING
            )
            st2 = Stage(
                id="st2", pipeline_id="p1", name="Deploy", order=1, status=StageStatus.PENDING
            )
            run = PipelineRun(id="run_skip", pipeline_id="p1", status="running", stages=(st1, st2))
            orchestrator._runs["run_skip"] = run
            skipped = await orchestrator.skip_stage("run_skip", "st2")
            assert skipped.status == StageStatus.SKIPPED
            updated = await orchestrator.get_run("run_skip")
            assert updated.stages[1].status == StageStatus.SKIPPED

        async def test_skip_not_pending(self, orchestrator: PipelineOrchestrator) -> None:
            st1 = Stage(id="st1", pipeline_id="p1", name="Build", order=0)
            pipe = Pipeline(id="p1", name="Pipeline", stages=(st1,))
            await orchestrator.create_pipeline(pipe)
            run = await orchestrator.run_pipeline("p1")
            with pytest.raises(StageExecutionError):
                await orchestrator.skip_stage(run.id, "st1")

    class TestCancelRun:
        async def test_cancel(self, orchestrator: PipelineOrchestrator) -> None:
            run = PipelineRun(id="run_test", pipeline_id="p1", status="running")
            orchestrator._runs["run_test"] = run
            cancelled = await orchestrator.cancel_run("run_test")
            assert cancelled.status == "cancelled"

        async def test_cancel_not_running(self, orchestrator: PipelineOrchestrator) -> None:
            st1 = Stage(id="st1", pipeline_id="p1", name="Build", order=0)
            pipe = Pipeline(id="p1", name="Pipeline", stages=(st1,))
            await orchestrator.create_pipeline(pipe)
            run = await orchestrator.run_pipeline("p1")
            with pytest.raises(OrchestratorError):
                await orchestrator.cancel_run(run.id)

    class TestConfig:
        def test_default_config(self) -> None:
            o = PipelineOrchestrator()
            assert o.config.max_concurrent_stages == 5
            assert o.config.default_timeout_seconds == 300

        def test_custom_config(self) -> None:
            config = OrchestratorConfig(max_concurrent_stages=10, default_timeout_seconds=600)
            o = PipelineOrchestrator(config=config)
            assert o.config.max_concurrent_stages == 10
            assert o.config.default_timeout_seconds == 600
