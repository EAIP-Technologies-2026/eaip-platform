"""Tests for configmgt validation."""

from __future__ import annotations

import pytest

from eaip.configmgt.models import ConfigEntry, ConfigEntryType
from eaip.configmgt.validation import ConfigValidator


class TestConfigValidator:
    @pytest.fixture
    def validator(self) -> ConfigValidator:
        return ConfigValidator()

    @pytest.mark.parametrize(
        ("entry", "expected_valid"),
        [
            (ConfigEntry(id="e1", key="k", value="hello", type=ConfigEntryType.STRING), True),
            (ConfigEntry(id="e2", key="k", value="42", type=ConfigEntryType.INTEGER), True),
            (ConfigEntry(id="e3", key="k", value="3.14", type=ConfigEntryType.FLOAT), True),
            (ConfigEntry(id="e4", key="k", value="true", type=ConfigEntryType.BOOLEAN), True),
            (ConfigEntry(id="e5", key="k", value='{"a":1}', type=ConfigEntryType.JSON), True),
            (ConfigEntry(id="e6", key="k", value="key: val", type=ConfigEntryType.YAML), True),
            (ConfigEntry(id="e7", key="k", value="not_int", type=ConfigEntryType.INTEGER), False),
            (ConfigEntry(id="e8", key="k", value="not_float", type=ConfigEntryType.FLOAT), False),
            (ConfigEntry(id="e9", key="k", value="{bad json", type=ConfigEntryType.JSON), False),
        ],
    )
    async def test_validate(
        self, validator: ConfigValidator, entry: ConfigEntry, expected_valid: bool
    ) -> None:
        result = await validator.validate(entry)
        assert result.valid is expected_valid
        assert result.entry_id == entry.id

    async def test_validate_returns_validation(self, validator: ConfigValidator) -> None:
        entry = ConfigEntry(id="e1", key="k", value="hello")
        result = await validator.validate(entry)
        assert result.id == "val_e1"
        assert result.entry_id == "e1"

    async def test_validate_type(self, validator: ConfigValidator) -> None:
        assert await validator.validate_type("hello", "string") is True
        assert await validator.validate_type(42, "int") is True
        assert await validator.validate_type(3.14, "float") is True
        assert await validator.validate_type("true", "bool") is True
        assert await validator.validate_type({"a": 1}, "json") is True
        assert await validator.validate_type({"key": "val"}, "yaml") is True
        assert await validator.validate_type("not_a_number", "int") is False
        assert await validator.validate_type("bad", "unknown") is False

    async def test_validate_enum(self, validator: ConfigValidator) -> None:
        assert await validator.validate_enum("prod", ("dev", "staging", "prod")) is True
        assert await validator.validate_enum("unknown", ("dev", "staging")) is False
        assert await validator.validate_enum(3, (1, 2, 3)) is True

    async def test_validate_range(self, validator: ConfigValidator) -> None:
        assert await validator.validate_range(5, 0, 10) is True
        assert await validator.validate_range(-1, 0, 10) is False
        assert await validator.validate_range(11, 0, 10) is False
        assert await validator.validate_range(5, None, 10) is True
        assert await validator.validate_range(5, 0, None) is True
        assert await validator.validate_range("not_a_number", 0, 10) is False

    async def test_validate_schema(self, validator: ConfigValidator) -> None:
        entry = ConfigEntry(
            id="e1", key="k", value='{"name": "test", "port": 8080}', type=ConfigEntryType.JSON
        )
        schema = {
            "name": {"required": True},
            "port": {"required": True},
            "extra": {"required": False},
        }
        result = await validator.validate_schema(entry, schema)
        assert result.valid is True

    async def test_validate_schema_missing_required(self, validator: ConfigValidator) -> None:
        entry = ConfigEntry(id="e1", key="k", value='{"name": "test"}', type=ConfigEntryType.JSON)
        schema = {"name": {"required": True}, "port": {"required": True}}
        result = await validator.validate_schema(entry, schema)
        assert result.valid is False
        assert "Missing required field" in result.errors[0]

    async def test_validate_schema_unparseable(self, validator: ConfigValidator) -> None:
        entry = ConfigEntry(id="e1", key="k", value="{bad}}", type=ConfigEntryType.JSON)
        result = await validator.validate_schema(entry, {"port": {"required": True}})
        assert result.valid is False
