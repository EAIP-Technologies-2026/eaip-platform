"""Tests for SchemaRegistry."""

from __future__ import annotations

import pytest

from eaip.schema.exceptions import (
    SchemaNotFoundError,
    SchemaVersionNotFoundError,
)
from eaip.schema.models import (
    SchemaConfig,
    SchemaDefinition,
    SchemaStatus,
    SchemaType,
    SchemaVersion,
)
from eaip.schema.registry import SchemaRegistry


class TestSchemaRegistry:
    def make_schema(
        self,
        id: str = "s1",
        name: str = "TestSchema",
        type: SchemaType = SchemaType.JSON_SCHEMA,
        version: str = "1.0.0",
    ) -> SchemaDefinition:
        return SchemaDefinition(
            id=id,
            name=name,
            type=type,
            version=version,
            schema_content='{"type": "object"}',
        )

    def make_version(
        self,
        id: str = "v1",
        schema_id: str = "s1",
        version: str = "1.0.0",
    ) -> SchemaVersion:
        return SchemaVersion(
            id=id, schema_id=schema_id, version=version, content='{"type": "object"}'
        )

    def test_register_and_get(self) -> None:
        reg = SchemaRegistry()
        schema = self.make_schema()
        reg.register(schema)
        assert reg.get("s1") == schema

    def test_register_duplicate(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema())
        with pytest.raises(ValueError, match="already exists"):
            reg.register(self.make_schema())

    def test_create_and_get(self) -> None:
        reg = SchemaRegistry()
        schema = reg.create(
            id="s1", name="NewSchema", type="avro", version="1.0.0", schema_content="{}"
        )
        assert schema.id == "s1"
        assert schema.name == "NewSchema"
        assert schema.type == SchemaType.AVRO

    def test_get_not_found(self) -> None:
        reg = SchemaRegistry()
        with pytest.raises(SchemaNotFoundError):
            reg.get("nonexistent")

    def test_update(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema())
        updated = reg.update("s1", description="Updated description")
        assert updated.description == "Updated description"
        assert reg.get("s1").description == "Updated description"

    def test_update_not_found(self) -> None:
        reg = SchemaRegistry()
        with pytest.raises(SchemaNotFoundError):
            reg.update("nonexistent", description="test")

    def test_delete(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema())
        reg.delete("s1")
        with pytest.raises(SchemaNotFoundError):
            reg.get("s1")

    def test_delete_not_found(self) -> None:
        reg = SchemaRegistry()
        with pytest.raises(SchemaNotFoundError):
            reg.delete("nonexistent")

    def test_list(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema(id="s1"))
        reg.register(self.make_schema(id="s2", name="Schema2"))
        schemas = reg.list_schemas()
        assert len(schemas) == 2
        assert {s.id for s in schemas} == {"s1", "s2"}

    def test_list_empty(self) -> None:
        reg = SchemaRegistry()
        assert reg.list_schemas() == []

    def test_create_version(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema())
        version = self.make_version()
        result = reg.create_version(version)
        assert result == version

    def test_create_version_schema_not_found(self) -> None:
        reg = SchemaRegistry()
        with pytest.raises(SchemaNotFoundError):
            reg.create_version(self.make_version())

    def test_create_version_duplicate(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema())
        reg.create_version(self.make_version())
        with pytest.raises(ValueError, match="already exists"):
            reg.create_version(self.make_version())

    def test_create_version_max_versions(self) -> None:
        config = SchemaConfig(max_versions=1)
        reg = SchemaRegistry(config=config)
        reg.register(self.make_schema())
        reg.create_version(self.make_version(version="1.0.0"))
        with pytest.raises(ValueError, match="Max versions"):
            reg.create_version(self.make_version(id="v2", version="2.0.0"))

    def test_get_version(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema())
        version = self.make_version()
        reg.create_version(version)
        assert reg.get_version("s1", "1.0.0") == version

    def test_get_version_not_found(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema())
        with pytest.raises(SchemaVersionNotFoundError):
            reg.get_version("s1", "nonexistent")

    def test_get_version_schema_not_found(self) -> None:
        reg = SchemaRegistry()
        with pytest.raises(SchemaNotFoundError):
            reg.get_version("nonexistent", "1.0.0")

    def test_list_versions(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema())
        v1 = self.make_version(version="1.0.0")
        v2 = self.make_version(id="v2", version="2.0.0")
        reg.create_version(v1)
        reg.create_version(v2)
        versions = reg.list_versions("s1")
        assert len(versions) == 2

    def test_list_versions_schema_not_found(self) -> None:
        reg = SchemaRegistry()
        with pytest.raises(SchemaNotFoundError):
            reg.list_versions("nonexistent")

    def test_list_versions_empty(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema())
        assert reg.list_versions("s1") == []

    def test_get_latest_version(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema())
        v1 = self.make_version(version="1.0.0")
        v2 = self.make_version(id="v2", version="2.0.0")
        reg.create_version(v1)
        reg.create_version(v2)
        latest = reg.get_latest_version("s1")
        assert latest.version == "2.0.0"

    def test_get_latest_version_no_versions(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema())
        with pytest.raises(SchemaVersionNotFoundError):
            reg.get_latest_version("s1")

    def test_deprecate_schema(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema())
        result = reg.deprecate_schema("s1")
        assert result.status == SchemaStatus.DEPRECATED
        assert reg.get("s1").status == SchemaStatus.DEPRECATED

    def test_supersede_schema(self) -> None:
        reg = SchemaRegistry()
        reg.register(self.make_schema())
        result = reg.supersede_schema("s1", superseded_by="s2")
        assert result.status == SchemaStatus.SUPERSEDED
        assert reg.get("s1").status == SchemaStatus.SUPERSEDED

    def test_config_property(self) -> None:
        config = SchemaConfig(max_versions=5)
        reg = SchemaRegistry(config=config)
        assert reg.config.max_versions == 5
