"""SdkManager — CRUD and lifecycle management for SDK definitions."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any

import anyio

from eaip.logging.context import get_logger
from eaip.sdk.events import (
    SdkBuildCompleted,
    SdkBuildFailed,
    SdkBuildStarted,
    SdkCreated,
    SdkDeprecated,
    SdkPublished,
)
from eaip.sdk.exceptions import BuildError, SdkNotFoundError
from eaip.sdk.models import BuildStatus, SdkBuild, SdkDefinition, SdkEndpoint, SdkStatus
from eaip.shared.time import utc_now

if TYPE_CHECKING:
    from eaip.events.bus import EventBus


class SdkManager:
    """Manages SDK definitions, endpoints, and build lifecycle."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._sdks: dict[str, SdkDefinition] = {}
        self._endpoints: dict[str, SdkEndpoint] = {}
        self._builds: dict[str, SdkBuild] = {}
        self._log = get_logger("eaip.sdk.manager")
        self._event_bus = event_bus

    # ------------------------------------------------------------------
    # SDK CRUD
    # ------------------------------------------------------------------

    def create_sdk(
        self,
        name: str,
        language: str,
        version: str,
        description: str = "",
        source_api_version: str = "",
        endpoints: tuple[str, ...] = (),
        models: tuple[str, ...] = (),
        config: dict[str, Any] | None = None,
        tags: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> SdkDefinition:
        sdk_id = f"sdk-{uuid.uuid4().hex[:12]}"
        now = utc_now()
        sdk = SdkDefinition(
            id=sdk_id,
            name=name,
            language=language,
            version=version,
            description=description,
            source_api_version=source_api_version,
            endpoints=endpoints,
            models=models,
            config=config or {},
            tags=tags,
            metadata=metadata or {},
            status=SdkStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )
        self._sdks[sdk_id] = sdk
        self._log.info("sdk.created", sdk_id=sdk_id, name=name, language=language)
        if self._event_bus is not None:
            anyio.from_thread.run(
                self._event_bus.publish,
                SdkCreated(sdk_id=sdk_id, name=name, language=language, version=version),
            )
        return sdk

    def get_sdk(self, sdk_id: str) -> SdkDefinition:
        if sdk_id not in self._sdks:
            raise SdkNotFoundError(f"SDK {sdk_id!r} not found", context={"sdk_id": sdk_id})
        return self._sdks[sdk_id]

    def update_sdk(self, sdk_id: str, **updates: Any) -> SdkDefinition:
        sdk = self.get_sdk(sdk_id)
        merged = sdk.model_copy(update={**updates, "updated_at": utc_now()}, deep=True)
        self._sdks[sdk_id] = merged
        self._log.info("sdk.updated", sdk_id=sdk_id)
        return merged

    def delete_sdk(self, sdk_id: str) -> None:
        if sdk_id not in self._sdks:
            raise SdkNotFoundError(f"SDK {sdk_id!r} not found", context={"sdk_id": sdk_id})
        del self._sdks[sdk_id]
        self._log.info("sdk.deleted", sdk_id=sdk_id)

    def list_sdks(
        self,
        language: str | None = None,
        status: SdkStatus | None = None,
    ) -> Sequence[SdkDefinition]:
        result = list(self._sdks.values())
        if language:
            result = [s for s in result if s.language == language]
        if status:
            result = [s for s in result if s.status == status]
        return result

    # ------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------

    def register_endpoint(
        self,
        path: str,
        method: str,
        description: str = "",
        parameters: tuple[str, ...] = (),
        request_schema: dict[str, Any] | None = None,
        response_schema: dict[str, Any] | None = None,
        auth_required: bool = True,
        tags: tuple[str, ...] = (),
    ) -> SdkEndpoint:
        endpoint_id = f"ep-{uuid.uuid4().hex[:12]}"
        endpoint = SdkEndpoint(
            id=endpoint_id,
            path=path,
            method=method.upper(),
            description=description,
            parameters=parameters,
            request_schema=request_schema or {},
            response_schema=response_schema or {},
            auth_required=auth_required,
            tags=tags,
        )
        self._endpoints[endpoint_id] = endpoint
        self._log.info("sdk.endpoint_registered", endpoint_id=endpoint_id, path=path)
        return endpoint

    def list_endpoints(self, sdk_id: str | None = None) -> Sequence[SdkEndpoint]:
        if sdk_id is None:
            return list(self._endpoints.values())
        sdk = self.get_sdk(sdk_id)
        return [ep for ep in self._endpoints.values() if ep.id in sdk.endpoints]

    # ------------------------------------------------------------------
    # Builds
    # ------------------------------------------------------------------

    def create_build(self, sdk_id: str, version: str) -> SdkBuild:
        self.get_sdk(sdk_id)
        build_id = f"bld-{uuid.uuid4().hex[:12]}"
        now = utc_now()
        build = SdkBuild(
            id=build_id,
            sdk_id=sdk_id,
            version=version,
            status=BuildStatus.PENDING,
            started_at=now,
        )
        self._builds[build_id] = build
        self._log.info("sdk.build.created", build_id=build_id, sdk_id=sdk_id)
        if self._event_bus is not None:
            anyio.from_thread.run(
                self._event_bus.publish,
                SdkBuildStarted(build_id=build_id, sdk_id=sdk_id, version=version),
            )
        return build

    async def get_build(self, build_id: str) -> SdkBuild:
        if build_id not in self._builds:
            raise BuildError(
                f"Build {build_id!r} not found",
                context={"build_id": build_id},
            )
        return self._builds[build_id]

    async def list_builds(self, sdk_id: str, limit: int = 20) -> Sequence[SdkBuild]:
        builds = [b for b in self._builds.values() if b.sdk_id == sdk_id]
        builds.sort(key=lambda b: b.started_at or datetime.min, reverse=True)
        return builds[:limit]

    async def publish_sdk(self, sdk_id: str, version: str) -> SdkDefinition:
        sdk = self.get_sdk(sdk_id)
        if sdk.status is SdkStatus.DEPRECATED:
            raise BuildError(
                f"Cannot publish deprecated SDK {sdk_id!r}",
                context={"sdk_id": sdk_id, "version": version},
            )
        build = self.create_build(sdk_id, version)
        try:
            completed_build = build.model_copy(
                update={
                    "status": BuildStatus.COMPLETED,
                    "completed_at": utc_now(),
                    "duration_ms": 100,
                },
            )
            self._builds[build.id] = completed_build
            published = sdk.model_copy(
                update={"status": SdkStatus.PUBLISHED, "updated_at": utc_now()},
            )
            self._sdks[sdk_id] = published
            self._log.info("sdk.published", sdk_id=sdk_id, version=version)
            if self._event_bus is not None:
                anyio.from_thread.run(
                    self._event_bus.publish,
                    SdkBuildCompleted(
                        build_id=build.id,
                        sdk_id=sdk_id,
                        version=version,
                        duration_ms=100,
                    ),
                )
                anyio.from_thread.run(
                    self._event_bus.publish,
                    SdkPublished(sdk_id=sdk_id, version=version),
                )
            return published
        except Exception as exc:
            failed = build.model_copy(
                update={
                    "status": BuildStatus.FAILED,
                    "completed_at": utc_now(),
                    "error": str(exc),
                },
            )
            self._builds[build.id] = failed
            if self._event_bus is not None:
                anyio.from_thread.run(
                    self._event_bus.publish,
                    SdkBuildFailed(
                        build_id=build.id,
                        sdk_id=sdk_id,
                        version=version,
                        error=str(exc),
                    ),
                )
            raise BuildError(str(exc), context={"sdk_id": sdk_id, "version": version}) from exc

    async def deprecate_sdk(self, sdk_id: str, version: str) -> SdkDefinition:
        sdk = self.get_sdk(sdk_id)
        deprecated = sdk.model_copy(
            update={"status": SdkStatus.DEPRECATED, "updated_at": utc_now()},
        )
        self._sdks[sdk_id] = deprecated
        self._log.info("sdk.deprecated", sdk_id=sdk_id, version=version)
        if self._event_bus is not None:
            anyio.from_thread.run(
                self._event_bus.publish,
                SdkDeprecated(sdk_id=sdk_id, version=version),
            )
        return deprecated
