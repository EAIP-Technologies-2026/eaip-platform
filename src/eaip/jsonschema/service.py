"""JSONSchemaService — manage, validate, and track JSON schema documents."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from eaip.jsonschema.events import (
    SchemaCreated,
    SchemaDeprecated,
    SchemaUpdated,
    ValidationPerformed,
)
from eaip.jsonschema.exceptions import SchemaNotFoundError
from eaip.jsonschema.models import (
    SchemaConfig,
    SchemaDocument,
    SchemaStatus,
    SchemaValidationResult,
)
from eaip.shared.time import utc_now

EventCallback = Callable[[Any], Any]


class JSONSchemaService:
    def __init__(
        self,
        config: SchemaConfig | None = None,
        event_callback: EventCallback | None = None,
    ) -> None:
        self._config = config or SchemaConfig()
        self._schemas: dict[str, SchemaDocument] = {}
        self._validations: dict[str, SchemaValidationResult] = {}
        self._event_callback = event_callback

    def set_event_callback(self, callback: EventCallback | None) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback:
            self._event_callback(event)

    async def create_schema(
        self,
        name: str,
        *,
        schema_definition: dict[str, object] | None = None,
        description: str = "",
    ) -> SchemaDocument:
        now = utc_now()
        doc = SchemaDocument(
            id=str(uuid.uuid4()),
            name=name,
            schema_definition=schema_definition or {},
            description=description,
            version=1,
            status=SchemaStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )
        self._schemas[doc.id] = doc
        self._emit(SchemaCreated(schema_id=doc.id, name=name))
        return doc

    async def get_schema(self, schema_id: str) -> SchemaDocument:
        if schema_id not in self._schemas:
            raise SchemaNotFoundError(schema_id)
        return self._schemas[schema_id]

    async def list_schemas(
        self,
        status: SchemaStatus | None = None,
    ) -> list[SchemaDocument]:
        all_schemas = list(self._schemas.values())
        if status:
            all_schemas = [s for s in all_schemas if s.status == status]
        return all_schemas

    async def update_schema(
        self,
        schema_id: str,
        *,
        schema_definition: dict[str, object] | None = None,
        description: str | None = None,
    ) -> SchemaDocument:
        existing = await self.get_schema(schema_id)
        old_version = existing.version

        updated = SchemaDocument(
            id=existing.id,
            name=existing.name,
            schema_definition=schema_definition
            if schema_definition is not None
            else existing.schema_definition,
            description=description if description is not None else existing.description,
            version=old_version + 1,
            status=existing.status,
            created_at=existing.created_at,
            updated_at=utc_now(),
        )
        self._schemas[schema_id] = updated
        self._emit(
            SchemaUpdated(
                schema_id=schema_id,
                name=existing.name,
                old_version=old_version,
                new_version=updated.version,
            )
        )
        return updated

    async def deprecate_schema(self, schema_id: str) -> SchemaDocument:
        existing = await self.get_schema(schema_id)
        updated = SchemaDocument(
            id=existing.id,
            name=existing.name,
            schema_definition=existing.schema_definition,
            description=existing.description,
            version=existing.version,
            status=SchemaStatus.DEPRECATED,
            created_at=existing.created_at,
            updated_at=utc_now(),
        )
        self._schemas[schema_id] = updated
        self._emit(SchemaDeprecated(schema_id=schema_id, name=existing.name))
        return updated

    async def activate_schema(self, schema_id: str) -> SchemaDocument:
        existing = await self.get_schema(schema_id)
        updated = SchemaDocument(
            id=existing.id,
            name=existing.name,
            schema_definition=existing.schema_definition,
            description=existing.description,
            version=existing.version,
            status=SchemaStatus.ACTIVE,
            created_at=existing.created_at,
            updated_at=utc_now(),
        )
        self._schemas[schema_id] = updated
        return updated

    async def validate(
        self,
        schema_id: str,
        document: dict[str, object],
        *,
        document_ref: str = "",
    ) -> SchemaValidationResult:
        schema_doc = await self.get_schema(schema_id)
        errors: list[str] = []
        valid = True

        if schema_doc.schema_definition:
            try:
                self._run_basic_validation(schema_doc.schema_definition, document, errors)
            except Exception as exc:
                errors.append(str(exc))

            if errors:
                valid = False

        result = SchemaValidationResult(
            id=str(uuid.uuid4()),
            schema_id=schema_id,
            document_ref=document_ref,
            valid=valid,
            errors=tuple(errors[: self._config.max_validation_errors]),
        )
        self._validations[result.id] = result
        self._emit(
            ValidationPerformed(
                schema_id=schema_id,
                validation_id=result.id,
                valid=valid,
                error_count=len(result.errors),
            )
        )
        return result

    def _run_basic_validation(
        self,
        schema: dict[str, object],
        document: dict[str, object],
        errors: list[str],
    ) -> None:
        if "required" in schema:
            required_fields = schema["required"]
            if isinstance(required_fields, list):
                for field in required_fields:
                    if field not in document:
                        errors.append(f"missing required field: {field!r}")

        if "properties" in schema:
            props = schema["properties"]
            if isinstance(props, dict):
                for field, definition in props.items():
                    if field in document:
                        value = document[field]
                        if isinstance(definition, dict):
                            expected_type = definition.get("type")
                            if expected_type and expected_type != "object":
                                type_map: dict[str, type[Any] | tuple[type[Any], ...]] = {
                                    "string": str,
                                    "integer": int,
                                    "number": (int, float),
                                    "boolean": bool,
                                    "array": list,
                                    "object": dict,
                                }
                                py_type = type_map.get(expected_type)
                                if py_type and not isinstance(value, py_type):
                                    errors.append(
                                        f"field {field!r}: expected {expected_type}, "
                                        f"got {type(value).__name__}"
                                    )

    async def get_validation(self, validation_id: str) -> SchemaValidationResult:
        if validation_id not in self._validations:
            raise RuntimeError(f"Validation not found: {validation_id}")
        return self._validations[validation_id]


__all__ = ["JSONSchemaService"]
