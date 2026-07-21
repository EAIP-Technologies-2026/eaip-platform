"""Schema registry — manage schema definitions and versions."""

from __future__ import annotations

from threading import Lock
from typing import Any

from eaip.schema.exceptions import (
    SchemaNotFoundError,
    SchemaVersionNotFoundError,
)
from eaip.schema.models import (
    SchemaConfig,
    SchemaDefinition,
    SchemaStatus,
    SchemaVersion,
)
from eaip.shared.time import utc_now


class SchemaRegistry:
    def __init__(self, config: SchemaConfig | None = None) -> None:
        self._config = config or SchemaConfig()
        self._schemas: dict[str, SchemaDefinition] = {}
        self._versions: dict[str, list[SchemaVersion]] = {}
        self._lock = Lock()

    @property
    def config(self) -> SchemaConfig:
        return self._config

    # ------------------------------------------------------------------
    # Schema CRUD
    # ------------------------------------------------------------------
    def register(self, schema: SchemaDefinition) -> SchemaDefinition:
        with self._lock:
            if schema.id in self._schemas:
                raise ValueError(f"Schema with id {schema.id!r} already exists")
            self._schemas[schema.id] = schema
            self._versions[schema.id] = []
        return schema

    def create(
        self,
        id: str,
        name: str,
        type: str,
        version: str,
        schema_content: str,
        **kwargs: Any,
    ) -> SchemaDefinition:
        from eaip.schema.models import SchemaType

        schema = SchemaDefinition(
            id=id,
            name=name,
            type=SchemaType(type),
            version=version,
            schema_content=schema_content,
            **kwargs,
        )
        return self.register(schema)

    def get(self, schema_id: str) -> SchemaDefinition:
        try:
            return self._schemas[schema_id]
        except KeyError:
            raise SchemaNotFoundError(
                f"Schema {schema_id!r} not found",
                context={"schema_id": schema_id},
            )

    def update(self, schema_id: str, **kwargs: Any) -> SchemaDefinition:
        with self._lock:
            existing = self.get(schema_id)
            updated = existing.model_copy(update={**kwargs, "updated_at": utc_now()})
            self._schemas[schema_id] = updated
        return updated

    def delete(self, schema_id: str) -> None:
        with self._lock:
            if schema_id not in self._schemas:
                raise SchemaNotFoundError(
                    f"Schema {schema_id!r} not found",
                    context={"schema_id": schema_id},
                )
            del self._schemas[schema_id]
            self._versions.pop(schema_id, None)

    def list_schemas(self) -> list[SchemaDefinition]:
        return list(self._schemas.values())

    # ------------------------------------------------------------------
    # Version management
    # ------------------------------------------------------------------
    def create_version(self, version: SchemaVersion) -> SchemaVersion:
        with self._lock:
            if version.schema_id not in self._schemas:
                raise SchemaNotFoundError(
                    f"Schema {version.schema_id!r} not found",
                    context={"schema_id": version.schema_id},
                )
            versions = self._versions[version.schema_id]
            if any(v.version == version.version for v in versions):
                raise ValueError(
                    f"Version {version.version!r} already exists for schema {version.schema_id!r}"
                )
            if self._config.max_versions > 0 and len(versions) >= self._config.max_versions:
                raise ValueError(
                    f"Max versions ({self._config.max_versions}) reached for schema {version.schema_id!r}"
                )
            versions.append(version)
        return version

    def get_version(self, schema_id: str, version: str) -> SchemaVersion:
        versions = self._versions.get(schema_id)
        if versions is None:
            raise SchemaNotFoundError(
                f"Schema {schema_id!r} not found",
                context={"schema_id": schema_id},
            )
        for v in versions:
            if v.version == version:
                return v
        raise SchemaVersionNotFoundError(
            f"Version {version!r} not found for schema {schema_id!r}",
            context={"schema_id": schema_id, "version": version},
        )

    def list_versions(self, schema_id: str) -> list[SchemaVersion]:
        if schema_id not in self._schemas:
            raise SchemaNotFoundError(
                f"Schema {schema_id!r} not found",
                context={"schema_id": schema_id},
            )
        return list(self._versions.get(schema_id, []))

    def get_latest_version(self, schema_id: str) -> SchemaVersion:
        versions = self.list_versions(schema_id)
        if not versions:
            raise SchemaVersionNotFoundError(
                f"No versions found for schema {schema_id!r}",
                context={"schema_id": schema_id},
            )
        return max(versions, key=lambda v: v.created_at)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def deprecate_schema(self, schema_id: str, reason: str = "") -> SchemaDefinition:
        return self.update(schema_id, status=SchemaStatus.DEPRECATED)

    def supersede_schema(
        self, schema_id: str, superseded_by: str, reason: str = ""
    ) -> SchemaDefinition:
        return self.update(schema_id, status=SchemaStatus.SUPERSEDED)


__all__ = ["SchemaRegistry"]
