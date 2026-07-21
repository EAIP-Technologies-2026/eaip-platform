"""Tests for SchemaValidator."""

from __future__ import annotations

import pytest

from eaip.schema.models import (
    SchemaDefinition,
    SchemaType,
    SchemaVersion,
)
from eaip.schema.registry import SchemaRegistry
from eaip.schema.validation import SchemaValidator


class TestSchemaValidator:
    @pytest.fixture
    def registry(self) -> SchemaRegistry:
        reg = SchemaRegistry()
        schema = SchemaDefinition(
            id="s1",
            name="TestSchema",
            type=SchemaType.JSON_SCHEMA,
            version="1.0.0",
            schema_content='{"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}, "required": ["name"]}',
        )
        reg.register(schema)
        version = SchemaVersion(
            id="v1",
            schema_id="s1",
            version="1.0.0",
            content='{"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}, "required": ["name"]}',
        )
        reg.create_version(version)
        return reg

    @pytest.fixture
    def validator(self, registry: SchemaRegistry) -> SchemaValidator:
        return SchemaValidator(registry)

    async def test_validate_valid_data(self, validator: SchemaValidator) -> None:
        data = {"name": "Alice", "age": 30}
        result = await validator.validate(data, "s1")
        assert result.valid is True
        assert result.errors == ()

    async def test_validate_invalid_data(self, validator: SchemaValidator) -> None:
        data = {"name": 123, "age": "thirty"}
        result = await validator.validate(data, "s1")
        assert result.valid is False
        assert len(result.errors) > 0

    async def test_validate_missing_required(self, validator: SchemaValidator) -> None:
        data = {"age": 30}
        result = await validator.validate(data, "s1")
        assert result.valid is False
        assert any("name" in e for e in result.errors)

    async def test_validate_with_specific_version(
        self, validator: SchemaValidator, registry: SchemaRegistry
    ) -> None:
        v2 = SchemaVersion(
            id="v2",
            schema_id="s1",
            version="2.0.0",
            content='{"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}',
        )
        registry.create_version(v2)
        data = {"name": "Bob"}
        result = await validator.validate(data, "s1", version="2.0.0")
        assert result.valid is True

    async def test_validate_with_schema_json_schema(self, validator: SchemaValidator) -> None:
        schema_content = (
            '{"type": "object", "properties": {"x": {"type": "number"}}, "required": ["x"]}'
        )
        result = await validator.validate_with_schema(
            {"x": 42}, schema_content, SchemaType.JSON_SCHEMA
        )
        assert result.valid is True

    async def test_validate_with_schema_invalid(self, validator: SchemaValidator) -> None:
        schema_content = (
            '{"type": "object", "properties": {"x": {"type": "number"}}, "required": ["x"]}'
        )
        result = await validator.validate_with_schema(
            {"x": "not-a-number"}, schema_content, SchemaType.JSON_SCHEMA
        )
        assert result.valid is False

    def test_validate_json_schema_direct(self, validator: SchemaValidator) -> None:
        schema = {
            "type": "object",
            "properties": {"email": {"type": "string"}},
            "required": ["email"],
        }
        result = validator.validate_json_schema({"email": "test@example.com"}, schema)
        assert result.valid is True

    def test_validate_json_schema_invalid(self, validator: SchemaValidator) -> None:
        schema = {
            "type": "object",
            "properties": {"count": {"type": "integer"}},
            "required": ["count"],
        }
        result = validator.validate_json_schema({"count": "bad"}, schema)
        assert result.valid is False

    def test_validate_basic_valid(self, validator: SchemaValidator) -> None:
        schema = (
            '{"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}'
        )
        result = validator.validate_basic({"name": "Alice"}, schema)
        assert result.valid is True

    def test_validate_basic_invalid_type(self, validator: SchemaValidator) -> None:
        schema = '{"type": "object", "properties": {"count": {"type": "integer"}}, "required": ["count"]}'
        result = validator.validate_basic({"count": "not-int"}, schema)
        assert result.valid is False

    def test_validate_basic_missing_required(self, validator: SchemaValidator) -> None:
        schema = (
            '{"type": "object", "properties": {"req": {"type": "string"}}, "required": ["req"]}'
        )
        result = validator.validate_basic({}, schema)
        assert result.valid is False

    def test_validate_basic_bad_schema(self, validator: SchemaValidator) -> None:
        result = validator.validate_basic({}, "not-json{")
        assert result.valid is False

    async def test_validate_avro_basic(self, validator: SchemaValidator) -> None:
        avro_schema = (
            '{"type": "record", "name": "Test", "fields": [{"name": "name", "type": "string"}]}'
        )
        result = await validator.validate_with_schema(
            {"name": "Alice"}, avro_schema, SchemaType.AVRO
        )
        assert result.valid is True

    async def test_validate_basic_type_for_non_json(self, validator: SchemaValidator) -> None:
        result = await validator.validate_with_schema(
            {"key": "val"}, '{"type": "object"}', SchemaType.XML
        )
        assert result.valid is True
