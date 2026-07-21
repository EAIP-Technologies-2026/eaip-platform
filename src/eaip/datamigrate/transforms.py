"""Data transformer — mapping, validation, dry-run for data migrations."""

from __future__ import annotations

from typing import Any

from eaip.datamigrate.events import DataTransformApplied, DataTransformValidated
from eaip.datamigrate.exceptions import TransformError, ValidationError
from eaip.datamigrate.models import DataTransform


class DataTransformer:
    def __init__(self) -> None:
        self._transforms: dict[str, DataTransform] = {}

    def register(self, transform: DataTransform) -> None:
        self._transforms[transform.id] = transform

    async def transform(self, data: Any, transform_id: str) -> Any:
        transform = self._transforms.get(transform_id)
        if transform is None:
            raise TransformError(
                f"Transform '{transform_id}' not found",
                context={"transform_id": transform_id},
            )

        mapped = await self.apply_mapping(data, transform.mapping_rules)

        valid, errors = await self.validate_transform(mapped, transform.validation_rules)
        if not valid:
            raise ValidationError(
                f"Transform '{transform_id}' validation failed",
                context={"transform_id": transform_id, "errors": errors},
            )

        DataTransformApplied(
            transform_id=transform.id,
            transform_name=transform.name,
            source_type=transform.source_type,
            target_type=transform.target_type,
        )

        return mapped

    async def apply_mapping(self, data: Any, rules: dict[str, Any]) -> Any:
        if not rules:
            return data

        if isinstance(data, dict):
            result: dict[str, Any] = {}
            for target_key, source_key in rules.items():
                if isinstance(source_key, str):
                    result[target_key] = data.get(source_key)
                elif callable(source_key):
                    result[target_key] = source_key(data)
                else:
                    result[target_key] = source_key
            return result

        if isinstance(data, list):
            return [await self.apply_mapping(item, rules) for item in data]

        return data

    async def validate_transform(self, data: Any, rules: dict[str, Any]) -> tuple[bool, list[str]]:
        errors: list[str] = []

        if not rules:
            return True, errors

        if not isinstance(data, dict):
            return False, ["Data must be a dict for validation"]

        for field, rule in rules.items():
            if field not in data:
                errors.append(f"Missing required field: {field}")
                continue

            value = data[field]

            if isinstance(rule, dict):
                if "required" in rule and rule["required"] and value is None:
                    errors.append(f"Field '{field}' is required but null")
                if "type" in rule:
                    expected = rule["type"]
                    if not isinstance(value, expected):
                        errors.append(
                            f"Field '{field}' expected type '{expected.__name__}', got '{type(value).__name__}'"
                        )
                if "min" in rule and isinstance(value, (int, float)):
                    if value < rule["min"]:
                        errors.append(
                            f"Field '{field}' value {value} is below minimum {rule['min']}"
                        )
                if "max" in rule and isinstance(value, (int, float)):
                    if value > rule["max"]:
                        errors.append(
                            f"Field '{field}' value {value} exceeds maximum {rule['max']}"
                        )
                if "pattern" in rule and isinstance(value, str):
                    import re

                    if not re.match(rule["pattern"], value):
                        errors.append(f"Field '{field}' does not match pattern {rule['pattern']}")

        DataTransformValidated(
            transform_id="",
            transform_name="",
            valid=len(errors) == 0,
            errors=errors,
        )

        return len(errors) == 0, errors

    async def dry_run(self, transform_id: str, sample_data: Any) -> dict[str, Any]:
        transform = self._transforms.get(transform_id)
        if transform is None:
            raise TransformError(
                f"Transform '{transform_id}' not found",
                context={"transform_id": transform_id},
            )

        mapped = await self.apply_mapping(sample_data, transform.mapping_rules)
        valid, errors = await self.validate_transform(mapped, transform.validation_rules)

        return {
            "transform_id": transform_id,
            "input": sample_data,
            "mapped": mapped,
            "valid": valid,
            "errors": errors,
        }
