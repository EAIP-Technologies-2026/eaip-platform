"""CIService — central service for managing CI pipelines and builds."""

from __future__ import annotations

from eaip.ciservice.events import BuildFailed, BuildStarted, PipelineCreated
from eaip.ciservice.exceptions import BuildNotFoundError, PipelineNotFoundError
from eaip.ciservice.models import (
    Build,
    BuildStatus,
    CIArtifact,
    CIConfig,
    Pipeline,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class CIService:
    def __init__(self, config: CIConfig | None = None) -> None:
        self._config = config or CIConfig()
        self._pipelines: dict[str, Pipeline] = {}
        self._builds: dict[str, Build] = {}
        self._artifacts: dict[str, CIArtifact] = {}
        self._log = get_logger("eaip.ciservice.service")

    @property
    def config(self) -> CIConfig:
        return self._config

    async def create_pipeline(self, pipeline: Pipeline) -> Pipeline:
        self._pipelines[pipeline.id] = pipeline
        event = PipelineCreated(
            pipeline_id=pipeline.id,
            name=pipeline.name,
            repo_url=pipeline.repo_url,
        )
        self._log.info("ciservice.pipeline.created", pipeline_id=pipeline.id)
        return pipeline

    async def start_build(self, pipeline_id: str, commit_sha: str) -> Build:
        pipeline = self._get_pipeline(pipeline_id)
        build_id = f"build_{pipeline_id}_{commit_sha[:8]}"
        build = Build(
            id=build_id,
            pipeline_id=pipeline_id,
            commit_sha=commit_sha,
            status=BuildStatus.RUNNING,
        )
        self._builds[build.id] = build
        event = BuildStarted(
            build_id=build.id,
            pipeline_id=pipeline_id,
            commit_sha=commit_sha,
        )
        self._log.info("ciservice.build.started", build_id=build.id)
        return build

    async def complete_build(self, build_id: str, status: BuildStatus) -> Build:
        build = self._get_build(build_id)
        updated = Build(
            id=build.id,
            pipeline_id=build.pipeline_id,
            commit_sha=build.commit_sha,
            status=status,
            started_at=build.started_at,
            completed_at=utc_now(),
            logs=build.logs,
            artifacts=build.artifacts,
        )
        self._builds[build_id] = updated
        if status == BuildStatus.FAILED:
            event = BuildFailed(
                build_id=build_id,
                pipeline_id=build.pipeline_id,
                reason="Build completed with failure status",
            )
        else:
            pass
        self._log.info("ciservice.build.completed", build_id=build_id, status=status)
        return updated

    async def add_artifact(self, artifact: CIArtifact) -> CIArtifact:
        self._artifacts[artifact.id] = artifact
        build = self._builds.get(artifact.build_id)
        if build is not None:
            updated = Build(
                id=build.id,
                pipeline_id=build.pipeline_id,
                commit_sha=build.commit_sha,
                status=build.status,
                started_at=build.started_at,
                completed_at=build.completed_at,
                logs=build.logs,
                artifacts=(*build.artifacts, artifact.id),
            )
            self._builds[build.id] = updated
        self._log.info("ciservice.artifact.added", artifact_id=artifact.id)
        return artifact

    async def get_pipeline(self, pipeline_id: str) -> Pipeline:
        return self._get_pipeline(pipeline_id)

    async def list_pipelines(self) -> list[Pipeline]:
        return list(self._pipelines.values())

    async def get_build(self, build_id: str) -> Build:
        return self._get_build(build_id)

    async def list_builds(self, pipeline_id: str | None = None) -> list[Build]:
        if pipeline_id is None:
            return list(self._builds.values())
        return [b for b in self._builds.values() if b.pipeline_id == pipeline_id]

    async def get_artifact(self, artifact_id: str) -> CIArtifact:
        artifact = self._artifacts.get(artifact_id)
        if artifact is None:
            raise ValueError(f"Artifact '{artifact_id}' not found")
        return artifact

    def _get_pipeline(self, pipeline_id: str) -> Pipeline:
        pipeline = self._pipelines.get(pipeline_id)
        if pipeline is None:
            raise PipelineNotFoundError(f"Pipeline '{pipeline_id}' not found")
        return pipeline

    def _get_build(self, build_id: str) -> Build:
        build = self._builds.get(build_id)
        if build is None:
            raise BuildNotFoundError(f"Build '{build_id}' not found")
        return build
