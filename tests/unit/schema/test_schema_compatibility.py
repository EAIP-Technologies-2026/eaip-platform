"""Tests for CompatibilityChecker."""

from __future__ import annotations

import pytest

from eaip.schema.compatibility import CompatibilityChecker
from eaip.schema.models import (
    CompatibilityType,
    SchemaDefinition,
    SchemaType,
    SchemaVersion,
)
from eaip.schema.registry import SchemaRegistry


class TestCompatibilityChecker:
    @pytest.fixture
    def registry(self) -> SchemaRegistry:
        reg = SchemaRegistry()
        schema = SchemaDefinition(
            id="s1",
            name="TestSchema",
            type=SchemaType.JSON_SCHEMA,
            version="1.0.0",
            schema_content='{"type": "object"}',
        )
        reg.register(schema)
        return reg

    @pytest.fixture
    def checker(self, registry: SchemaRegistry) -> CompatibilityChecker:
        return CompatibilityChecker(registry)

    def add_version(
        self, registry: SchemaRegistry, version: str, fields: list[dict], schema_id: str = "s1"
    ) -> None:
        schema_obj = {
            "type": "object",
            "properties": {f["name"]: {"type": f.get("type", "string")} for f in fields},
            "required": [f["name"] for f in fields if f.get("required", False)],
        }
        import json

        content = json.dumps(schema_obj)
        v = SchemaVersion(
            id=f"v{version.replace('.', '_')}",
            schema_id=schema_id,
            version=version,
            content=content,
        )
        registry.create_version(v)

    async def test_none_compatibility_always_compatible(
        self, registry: SchemaRegistry, checker: CompatibilityChecker
    ) -> None:
        self.add_version(registry, "1.0.0", [{"name": "name", "type": "string", "required": True}])
        self.add_version(registry, "2.0.0", [])
        result = await checker.check_compatibility("s1", "1.0.0", "2.0.0", CompatibilityType.NONE)
        assert result.compatible is True

    async def test_backward_compatible(
        self, registry: SchemaRegistry, checker: CompatibilityChecker
    ) -> None:
        self.add_version(registry, "1.0.0", [{"name": "name", "type": "string", "required": True}])
        self.add_version(
            registry,
            "2.0.0",
            [
                {"name": "name", "type": "string", "required": True},
                {"name": "age", "type": "integer"},
            ],
        )
        result = await checker.check_compatibility(
            "s1", "1.0.0", "2.0.0", CompatibilityType.BACKWARD
        )
        assert result.compatible is True

    async def test_backward_incompatible_removed_field(
        self, registry: SchemaRegistry, checker: CompatibilityChecker
    ) -> None:
        self.add_version(registry, "1.0.0", [{"name": "name", "type": "string", "required": True}])
        self.add_version(registry, "2.0.0", [])
        result = await checker.check_compatibility(
            "s1", "1.0.0", "2.0.0", CompatibilityType.BACKWARD
        )
        assert result.compatible is False
        assert any("removed" in v.lower() for v in result.violations)

    async def test_backward_incompatible_new_required(
        self, registry: SchemaRegistry, checker: CompatibilityChecker
    ) -> None:
        self.add_version(registry, "1.0.0", [{"name": "name", "type": "string"}])
        self.add_version(
            registry,
            "2.0.0",
            [
                {"name": "name", "type": "string"},
                {"name": "age", "type": "integer", "required": True},
            ],
        )
        result = await checker.check_compatibility(
            "s1", "1.0.0", "2.0.0", CompatibilityType.BACKWARD
        )
        assert result.compatible is False
        assert any("required" in v.lower() for v in result.violations)

    async def test_forward_compatible(
        self, registry: SchemaRegistry, checker: CompatibilityChecker
    ) -> None:
        self.add_version(
            registry,
            "1.0.0",
            [
                {"name": "name", "type": "string", "required": True},
                {"name": "extra", "type": "string"},
            ],
        )
        self.add_version(registry, "2.0.0", [{"name": "name", "type": "string", "required": True}])
        result = await checker.check_compatibility(
            "s1", "1.0.0", "2.0.0", CompatibilityType.FORWARD
        )
        assert result.compatible is True

    async def test_forward_incompatible_added_field(
        self, registry: SchemaRegistry, checker: CompatibilityChecker
    ) -> None:
        self.add_version(registry, "1.0.0", [{"name": "name", "type": "string"}])
        self.add_version(
            registry,
            "2.0.0",
            [
                {"name": "name", "type": "string"},
                {"name": "age", "type": "integer"},
            ],
        )
        result = await checker.check_compatibility(
            "s1", "1.0.0", "2.0.0", CompatibilityType.FORWARD
        )
        assert result.compatible is False
        assert any("added" in v.lower() for v in result.violations)

    async def test_full_compatible(
        self, registry: SchemaRegistry, checker: CompatibilityChecker
    ) -> None:
        self.add_version(registry, "1.0.0", [{"name": "name", "type": "string", "required": True}])
        self.add_version(registry, "2.0.0", [{"name": "name", "type": "string", "required": True}])
        result = await checker.check_compatibility("s1", "1.0.0", "2.0.0", CompatibilityType.FULL)
        assert result.compatible is True

    async def test_full_incompatible(
        self, registry: SchemaRegistry, checker: CompatibilityChecker
    ) -> None:
        self.add_version(registry, "1.0.0", [{"name": "name", "type": "string"}])
        self.add_version(
            registry,
            "2.0.0",
            [
                {"name": "name", "type": "string"},
                {"name": "age", "type": "integer"},
            ],
        )
        result = await checker.check_compatibility("s1", "1.0.0", "2.0.0", CompatibilityType.FULL)
        assert result.compatible is False

    async def test_schema_not_found(
        self, registry: SchemaRegistry, checker: CompatibilityChecker
    ) -> None:
        with pytest.raises(Exception):
            await checker.check_compatibility("nonexistent", "1", "2")

    async def test_version_not_found(
        self, registry: SchemaRegistry, checker: CompatibilityChecker
    ) -> None:
        self.add_version(registry, "1.0.0", [{"name": "name", "type": "string"}])
        with pytest.raises(Exception):
            await checker.check_compatibility("s1", "1.0.0", "99.0.0")
