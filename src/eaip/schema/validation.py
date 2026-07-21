"""Schema validation — validate data against registered schemas."""

from __future__ import annotations

import json
from typing import Any

from eaip.schema.models import (
    SchemaType,
    SchemaValidationResult,
)
from eaip.schema.registry import SchemaRegistry


class SchemaValidator:
    def __init__(self, registry: SchemaRegistry) -> None:
        self._registry = registry

    async def validate(
        self, data: dict[str, Any], schema_id: str, version: str | None = None
    ) -> SchemaValidationResult:
        if version:
            schema_version = self._registry.get_version(schema_id, version)
            schema_content = schema_version.content
            schema_def = self._registry.get(schema_id)
            schema_type = schema_def.type
        else:
            schema_def = self._registry.get(schema_id)
            schema_content = schema_def.schema_content
            schema_type = schema_def.type

        return await self.validate_with_schema(data, schema_content, schema_type)

    async def validate_with_schema(
        self, data: dict[str, Any], schema_content: str, schema_type: SchemaType
    ) -> SchemaValidationResult:
        import uuid

        result_id = str(uuid.uuid4())

        if schema_type == SchemaType.JSON_SCHEMA:
            return self._validate_json_schema(data, schema_content, result_id)
        if schema_type == SchemaType.AVRO:
            return self._validate_avro(data, schema_content, result_id)
        return self.validate_basic(data, schema_content)

    def _validate_json_schema(
        self, data: dict[str, Any], schema_content: str, result_id: str
    ) -> SchemaValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        try:
            schema = json.loads(schema_content)
        except json.JSONDecodeError as e:
            return SchemaValidationResult(
                id=result_id,
                schema_id="",
                valid=False,
                errors=(f"Invalid JSON schema: {e}",),
            )

        try:
            import jsonschema

            validator = jsonschema.Draft7Validator(schema)
            validation_errors = list(validator.iter_errors(data))
            if validation_errors:
                for ve in validation_errors:
                    errors.append(ve.message)
        except ImportError:
            warnings.append("jsonschema library not available; performing basic validation")
            errors.extend(self._check_basic_json(data, schema))

        return SchemaValidationResult(
            id=result_id,
            schema_id="",
            valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=tuple(warnings),
            data_sample=data,
        )

    def _validate_avro(
        self, data: dict[str, Any], schema_content: str, result_id: str
    ) -> SchemaValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        try:
            import fastavro

            schema = json.loads(schema_content)
            fastavro.validate(data, schema)
        except ImportError:
            warnings.append("fastavro library not available; performing basic validation")
            try:
                schema = json.loads(schema_content)
                errors.extend(self._check_basic_json(data, schema))
            except json.JSONDecodeError as e:
                errors.append(f"Invalid Avro schema: {e}")
        except Exception as e:
            errors.append(str(e))

        return SchemaValidationResult(
            id=result_id,
            schema_id="",
            valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=tuple(warnings),
            data_sample=data,
        )

    def validate_json_schema(
        self, data: dict[str, Any], schema: dict[str, Any]
    ) -> SchemaValidationResult:
        import uuid

        result_id = str(uuid.uuid4())
        errors: list[str] = []

        try:
            import jsonschema

            validator = jsonschema.Draft7Validator(schema)
            validation_errors = list(validator.iter_errors(data))
            if validation_errors:
                for ve in validation_errors:
                    errors.append(ve.message)
        except ImportError:
            errors.extend(self._check_basic_json(data, schema))

        return SchemaValidationResult(
            id=result_id,
            schema_id="",
            valid=len(errors) == 0,
            errors=tuple(errors),
            data_sample=data,
        )

    def validate_avro(self, data: dict[str, Any], schema: dict[str, Any]) -> SchemaValidationResult:
        import uuid

        result_id = str(uuid.uuid4())
        errors: list[str] = []

        try:
            import fastavro

            fastavro.validate(data, schema)
        except ImportError:
            errors.extend(self._check_basic_json(data, schema))
        except Exception as e:
            errors.append(str(e))

        return SchemaValidationResult(
            id=result_id,
            schema_id="",
            valid=len(errors) == 0,
            errors=tuple(errors),
            data_sample=data,
        )

    def validate_basic(self, data: dict[str, Any], schema_content: str) -> SchemaValidationResult:
        import uuid

        result_id = str(uuid.uuid4())
        try:
            schema = json.loads(schema_content)
        except json.JSONDecodeError as e:
            return SchemaValidationResult(
                id=result_id,
                schema_id="",
                valid=False,
                errors=(f"Invalid schema: {e}",),
            )
        errors = self._check_basic_json(data, schema)
        return SchemaValidationResult(
            id=result_id,
            schema_id="",
            valid=len(errors) == 0,
            errors=tuple(errors),
            data_sample=data,
        )

    def _check_basic_json(self, data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        properties = schema.get("properties", schema.get("fields", {}))
        if isinstance(properties, list):
            for field in properties:
                field_name = field.get("name", "")
                field_type = field.get("type", "")
                required = field.get("required", False)
                if field_name in data:
                    val = data[field_name]
                    if isinstance(field_type, str) and field_type != "null":
                        type_map = {
                            "string": str,
                            "integer": int,
                            "number": (int, float),
                            "boolean": bool,
                            "object": dict,
                            "array": list,
                        }
                        expected = type_map.get(field_type)
                        if expected and not isinstance(val, expected):  # type: ignore[arg-type]
                            errors.append(
                                f"Field {field_name!r}: expected {field_type}, got {type(val).__name__}"
                            )
                elif required:
                    errors.append(f"Required field {field_name!r} is missing")
        elif isinstance(properties, dict):
            required_fields = schema.get("required", [])
            for field_name, field_schema in properties.items():
                if field_name in data:
                    val = data[field_name]
                    field_type = field_schema
                    if isinstance(field_type, dict):
                        field_type = field_type.get("type", "")
                    if isinstance(field_type, str):
                        type_map = {
                            "string": str,
                            "integer": int,
                            "number": (int, float),
                            "boolean": bool,
                            "object": dict,
                            "array": list,
                        }
                        expected = type_map.get(field_type)
                        if expected and not isinstance(val, expected):  # type: ignore[arg-type]
                            errors.append(
                                f"Field {field_name!r}: expected {field_type}, got {type(val).__name__}"
                            )
                elif field_name in required_fields:
                    errors.append(f"Required field {field_name!r} is missing")
        return errors


__all__ = ["SchemaValidator"]
