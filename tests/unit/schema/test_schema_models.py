"""Tests for schema models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.schema.models import (
    CompatibilityResult,
    CompatibilityType,
    SchemaConfig,
    SchemaDefinition,
    SchemaStatus,
    SchemaType,
    SchemaValidationResult,
    SchemaVersion,
)


class TestSchemaDefinition:
    def test_minimal(self) -> None:
        s = SchemaDefinition(
            id="s1",
            name="TestSchema",
            type=SchemaType.JSON_SCHEMA,
            version="1.0.0",
            schema_content='{"type": "object"}',
        )
        assert s.id == "s1"
        assert s.name == "TestSchema"
        assert s.type == SchemaType.JSON_SCHEMA
        assert s.version == "1.0.0"
        assert s.schema_content == '{"type": "object"}'
        assert s.description == ""
        assert s.tags == ()
        assert s.metadata == {}
        assert s.status == SchemaStatus.ACTIVE

    def test_frozen(self) -> None:
        s = SchemaDefinition(
            id="s1",
            name="T",
            type=SchemaType.AVRO,
            version="1",
            schema_content="{}",
        )
        with pytest.raises(ValidationError):
            s.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            SchemaDefinition(
                id="s1",
                name="T",
                type=SchemaType.AVRO,
                version="1",
                schema_content="{}",
                unknown=True,
            )

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        s = SchemaDefinition(
            id="s1",
            name="FullSchema",
            type=SchemaType.PROTOBUF,
            version="2.0.0",
            schema_content='syntax = "proto3";',
            description="A full schema",
            tags=("proto", "v2"),
            metadata={"owner": "team-a"},
            created_at=ts,
            updated_at=ts,
            status=SchemaStatus.DEPRECATED,
        )
        assert s.description == "A full schema"
        assert s.tags == ("proto", "v2")
        assert s.metadata == {"owner": "team-a"}
        assert s.created_at == ts
        assert s.updated_at == ts
        assert s.status == SchemaStatus.DEPRECATED

    def test_all_types(self) -> None:
        for st in SchemaType:
            s = SchemaDefinition(
                id=st.value, name=st.value, type=st, version="1", schema_content="{}"
            )
            assert s.type == st

    def test_all_statuses(self) -> None:
        for ss in SchemaStatus:
            s = SchemaDefinition(
                id=ss.value,
                name=ss.value,
                type=SchemaType.JSON_SCHEMA,
                version="1",
                schema_content="{}",
                status=ss,
            )
            assert s.status == ss


class TestSchemaVersion:
    def test_minimal(self) -> None:
        v = SchemaVersion(id="v1", schema_id="s1", version="1.0.0", content="{}")
        assert v.id == "v1"
        assert v.schema_id == "s1"
        assert v.version == "1.0.0"
        assert v.content == "{}"
        assert v.compatibility == CompatibilityType.BACKWARD
        assert v.change_log == ""
        assert v.author == ""
        assert v.metadata == {}

    def test_frozen(self) -> None:
        v = SchemaVersion(id="v1", schema_id="s1", version="1", content="{}")
        with pytest.raises(ValidationError):
            v.version = "2"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            SchemaVersion(id="v1", schema_id="s1", version="1", content="{}", unknown=True)

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        v = SchemaVersion(
            id="v1",
            schema_id="s1",
            version="2.0.0",
            content='{"type": "object"}',
            compatibility=CompatibilityType.FULL,
            change_log="Added field",
            created_at=ts,
            author="user-1",
            metadata={"reviewed": True},
        )
        assert v.compatibility == CompatibilityType.FULL
        assert v.change_log == "Added field"
        assert v.created_at == ts
        assert v.author == "user-1"
        assert v.metadata == {"reviewed": True}

    def test_all_compatibility_types(self) -> None:
        for ct in CompatibilityType:
            v = SchemaVersion(
                id=ct.value, schema_id="s1", version="1", content="{}", compatibility=ct
            )
            assert v.compatibility == ct


class TestCompatibilityResult:
    def test_minimal(self) -> None:
        r = CompatibilityResult(
            id="r1",
            schema_id="s1",
            source_version="1",
            target_version="2",
            compatible=True,
        )
        assert r.id == "r1"
        assert r.compatible is True
        assert r.violations == ()
        assert r.check_type == CompatibilityType.BACKWARD
        assert r.metadata == {}

    def test_frozen(self) -> None:
        r = CompatibilityResult(
            id="r1", schema_id="s1", source_version="1", target_version="2", compatible=True
        )
        with pytest.raises(ValidationError):
            r.compatible = False

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            CompatibilityResult(
                id="r1",
                schema_id="s1",
                source_version="1",
                target_version="2",
                compatible=True,
                unknown=True,
            )

    def test_full(self) -> None:
        r = CompatibilityResult(
            id="r1",
            schema_id="s1",
            source_version="1",
            target_version="2",
            compatible=False,
            violations=("Field removed",),
            check_type=CompatibilityType.FULL,
            metadata={"env": "test"},
        )
        assert r.compatible is False
        assert r.violations == ("Field removed",)
        assert r.check_type == CompatibilityType.FULL
        assert r.metadata == {"env": "test"}

    def test_all_check_types(self) -> None:
        for ct in CompatibilityType:
            r = CompatibilityResult(
                id=ct.value,
                schema_id="s1",
                source_version="1",
                target_version="2",
                compatible=True,
                check_type=ct,
            )
            assert r.check_type == ct


class TestSchemaValidationResult:
    def test_minimal(self) -> None:
        r = SchemaValidationResult(id="r1", schema_id="s1", valid=True)
        assert r.valid is True
        assert r.errors == ()
        assert r.warnings == ()
        assert r.data_sample is None

    def test_frozen(self) -> None:
        r = SchemaValidationResult(id="r1", schema_id="s1", valid=True)
        with pytest.raises(ValidationError):
            r.valid = False

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            SchemaValidationResult(id="r1", schema_id="s1", valid=True, unknown=True)

    def test_full(self) -> None:
        r = SchemaValidationResult(
            id="r1",
            schema_id="s1",
            valid=False,
            errors=("missing field",),
            warnings=("deprecated",),
            data_sample={"key": "val"},
        )
        assert r.valid is False
        assert r.errors == ("missing field",)
        assert r.warnings == ("deprecated",)
        assert r.data_sample == {"key": "val"}


class TestSchemaConfig:
    def test_defaults(self) -> None:
        c = SchemaConfig()
        assert c.default_compatibility == CompatibilityType.BACKWARD
        assert c.enable_validation is True
        assert c.enable_evolution is True
        assert c.max_versions == 100
        assert c.cache_ttl_seconds == 300

    def test_custom(self) -> None:
        c = SchemaConfig(
            default_compatibility=CompatibilityType.FULL,
            enable_validation=False,
            enable_evolution=False,
            max_versions=10,
            cache_ttl_seconds=60,
        )
        assert c.default_compatibility == CompatibilityType.FULL
        assert c.enable_validation is False
        assert c.enable_evolution is False
        assert c.max_versions == 10
        assert c.cache_ttl_seconds == 60

    def test_frozen(self) -> None:
        c = SchemaConfig()
        with pytest.raises(ValidationError):
            c.max_versions = 50

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            SchemaConfig(unknown=True)

    def test_all_compatibility_types(self) -> None:
        for ct in CompatibilityType:
            c = SchemaConfig(default_compatibility=ct)
            assert c.default_compatibility == ct
