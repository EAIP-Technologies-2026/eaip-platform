"""Tests for :mod:`eaip.ciservice.service`."""

from __future__ import annotations

import pytest

from eaip.ciservice.exceptions import BuildNotFoundError, PipelineNotFoundError
from eaip.ciservice.models import Build, BuildStatus, CIArtifact, CIConfig, Pipeline
from eaip.ciservice.service import CIService


class TestCIService:
    @pytest.fixture
    def service(self) -> CIService:
        return CIService()

    @pytest.fixture
    def sample_pipeline(self) -> Pipeline:
        return Pipeline(
            id="p1",
            name="Test Pipeline",
            repo_url="https://github.com/org/repo",
            steps=("lint", "test", "build"),
        )

    class TestCreatePipeline:
        async def test_create(self, service: CIService, sample_pipeline: Pipeline) -> None:
            result = await service.create_pipeline(sample_pipeline)
            assert result.id == "p1"
            assert result.name == "Test Pipeline"

        async def test_list_pipelines(self, service: CIService, sample_pipeline: Pipeline) -> None:
            await service.create_pipeline(sample_pipeline)
            pipelines = await service.list_pipelines()
            assert len(pipelines) == 1

    class TestStartBuild:
        async def test_start(self, service: CIService, sample_pipeline: Pipeline) -> None:
            await service.create_pipeline(sample_pipeline)
            build = await service.start_build("p1", "abc123")
            assert build.status == BuildStatus.RUNNING
            assert build.commit_sha == "abc123"

        async def test_start_pipeline_not_found(self, service: CIService) -> None:
            with pytest.raises(PipelineNotFoundError):
                await service.start_build("nonexistent", "abc123")

    class TestCompleteBuild:
        async def test_complete_success(
            self, service: CIService, sample_pipeline: Pipeline
        ) -> None:
            await service.create_pipeline(sample_pipeline)
            build = await service.start_build("p1", "abc123")
            result = await service.complete_build(build.id, BuildStatus.SUCCEEDED)
            assert result.status == BuildStatus.SUCCEEDED
            assert result.completed_at is not None

        async def test_complete_failed(self, service: CIService, sample_pipeline: Pipeline) -> None:
            await service.create_pipeline(sample_pipeline)
            build = await service.start_build("p1", "abc123")
            result = await service.complete_build(build.id, BuildStatus.FAILED)
            assert result.status == BuildStatus.FAILED

        async def test_complete_not_found(self, service: CIService) -> None:
            with pytest.raises(BuildNotFoundError):
                await service.complete_build("nonexistent", BuildStatus.SUCCEEDED)

    class TestArtifact:
        async def test_add_artifact(self, service: CIService, sample_pipeline: Pipeline) -> None:
            await service.create_pipeline(sample_pipeline)
            build = await service.start_build("p1", "abc123")
            artifact = CIArtifact(
                id="a1",
                build_id=build.id,
                name="dist.zip",
                url="https://artifacts.example.com/dist.zip",
            )
            result = await service.add_artifact(artifact)
            assert result.name == "dist.zip"

        async def test_get_artifact(self, service: CIService) -> None:
            artifact = CIArtifact(
                id="a1", build_id="b1", name="dist.zip", url="https://example.com/dist.zip"
            )
            await service.add_artifact(artifact)
            result = await service.get_artifact("a1")
            assert result.name == "dist.zip"

    class TestGetPipeline:
        async def test_get(self, service: CIService, sample_pipeline: Pipeline) -> None:
            await service.create_pipeline(sample_pipeline)
            p = await service.get_pipeline("p1")
            assert p.repo_url == "https://github.com/org/repo"

        async def test_not_found(self, service: CIService) -> None:
            with pytest.raises(PipelineNotFoundError):
                await service.get_pipeline("nonexistent")

    class TestGetBuild:
        async def test_get(self, service: CIService, sample_pipeline: Pipeline) -> None:
            await service.create_pipeline(sample_pipeline)
            build = await service.start_build("p1", "abc123")
            b = await service.get_build(build.id)
            assert b.status == BuildStatus.RUNNING

        async def test_not_found(self, service: CIService) -> None:
            with pytest.raises(BuildNotFoundError):
                await service.get_build("nonexistent")

    class TestListBuilds:
        async def test_list_all(self, service: CIService, sample_pipeline: Pipeline) -> None:
            await service.create_pipeline(sample_pipeline)
            await service.start_build("p1", "abc123")
            builds = await service.list_builds()
            assert len(builds) == 1

        async def test_list_by_pipeline(
            self, service: CIService, sample_pipeline: Pipeline
        ) -> None:
            await service.create_pipeline(sample_pipeline)
            await service.start_build("p1", "abc123")
            builds = await service.list_builds(pipeline_id="p1")
            assert len(builds) == 1

    class TestConfig:
        def test_default_config(self) -> None:
            s = CIService()
            assert s.config.max_concurrent_builds == 5
            assert s.config.default_timeout_minutes == 30

        def test_custom_config(self) -> None:
            config = CIConfig(max_concurrent_builds=10, log_retention_days=60)
            s = CIService(config=config)
            assert s.config.max_concurrent_builds == 10
            assert s.config.log_retention_days == 60
