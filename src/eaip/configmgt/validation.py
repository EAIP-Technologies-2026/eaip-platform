"""Config validators — type, schema, enum, range checks."""

from __future__ import annotations

import json
from typing import Any

import yaml  # type: ignore[import-untyped]

from eaip.configmgt.models import ConfigEntry, ConfigEntryType, ConfigValidation


class ConfigValidator:
    async def validate(self, entry: ConfigEntry) -> ConfigValidation:
        errors: list[str] = []
        warnings: list[str] = []

        # type-based parsing check
        parsed = await self._try_parse(entry)
        if parsed is None:
            errors.append(f"Cannot parse value as {entry.type.value}")
        elif entry.type is ConfigEntryType.INTEGER and not isinstance(parsed, int):
            errors.append(f"Expected integer, got {type(parsed).__name__}")

        # status consistency
        if entry.status.value == "archived" and entry.version > 1:
            warnings.append("Archived entry has version > 1")

        return ConfigValidation(
            id=f"val_{entry.id}",
            entry_id=entry.id,
            valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=tuple(warnings),
            metadata={"validated_type": entry.type.value},
        )

    async def validate_schema(self, entry: ConfigEntry, schema: dict[str, Any]) -> ConfigValidation:
        errors: list[str] = []
        warnings: list[str] = []

        parsed = await self._try_parse(entry)
        if parsed is None:
            errors.append("Cannot parse value for schema validation")
            return ConfigValidation(
                id=f"val_schema_{entry.id}",
                entry_id=entry.id,
                valid=False,
                errors=tuple(errors),
                warnings=tuple(warnings),
            )

        if isinstance(parsed, dict):
            for key in schema:
                if key not in parsed:
                    if schema[key].get("required", False):
                        errors.append(f"Missing required field: {key}")
                    else:
                        warnings.append(f"Missing optional field: {key}")

        return ConfigValidation(
            id=f"val_schema_{entry.id}",
            entry_id=entry.id,
            valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=tuple(warnings),
            metadata={"schema_fields": list(schema.keys())},
        )

    async def _try_parse(self, entry: ConfigEntry) -> Any:
        try:
            match entry.type:
                case ConfigEntryType.STRING:
                    return entry.value
                case ConfigEntryType.INTEGER:
                    return int(entry.value)
                case ConfigEntryType.BOOLEAN:
                    return entry.value.lower() in ("true", "1", "yes")
                case ConfigEntryType.FLOAT:
                    return float(entry.value)
                case ConfigEntryType.JSON:
                    return json.loads(entry.value)
                case ConfigEntryType.YAML:
                    return yaml.safe_load(entry.value)
        except (ValueError, json.JSONDecodeError, yaml.YAMLError):
            return None

    async def validate_type(self, value: Any, expected_type: str) -> bool:
        try:
            match expected_type:
                case "string":
                    return isinstance(value, str)
                case "int":
                    int(value)
                    return True
                case "bool":
                    return isinstance(value, bool) or str(value).lower() in (
                        "true",
                        "false",
                        "0",
                        "1",
                    )
                case "float":
                    float(value)
                    return True
                case "json":
                    if isinstance(value, (dict, list)):
                        return True
                    json.loads(str(value))
                    return True
                case "yaml":
                    if isinstance(value, (dict, list)):
                        return True
                    yaml.safe_load(str(value))
                    return True
                case _:
                    return False
        except (ValueError, TypeError, json.JSONDecodeError, yaml.YAMLError):
            return False

    async def validate_enum(self, value: Any, allowed_values: tuple[Any, ...]) -> bool:
        return value in allowed_values

    async def validate_range(
        self, value: Any, min_val: float | None, max_val: float | None
    ) -> bool:
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False
            return not (max_val is not None and num > max_val)
        except (ValueError, TypeError):
            return False


__all__ = ["ConfigValidator"]
