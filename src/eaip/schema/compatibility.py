"""Schema compatibility checking — backward, forward, full, none."""

from __future__ import annotations

import json
from typing import Any

from eaip.schema.exceptions import SchemaNotFoundError
from eaip.schema.models import (
    CompatibilityResult,
    CompatibilityType,
    SchemaVersion,
)
from eaip.schema.registry import SchemaRegistry


class CompatibilityChecker:
    def __init__(self, registry: SchemaRegistry) -> None:
        self._registry = registry

    async def check_compatibility(
        self,
        schema_id: str,
        source_version: str,
        target_version: str,
        type: CompatibilityType = CompatibilityType.BACKWARD,
    ) -> CompatibilityResult:
        import uuid

        if schema_id not in self._registry._schemas:
            raise SchemaNotFoundError(
                f"Schema {schema_id!r} not found",
                context={"schema_id": schema_id},
            )

        source = self._registry.get_version(schema_id, source_version)
        target = self._registry.get_version(schema_id, target_version)

        result_id = str(uuid.uuid4())

        if type == CompatibilityType.NONE:
            return CompatibilityResult(
                id=result_id,
                schema_id=schema_id,
                source_version=source_version,
                target_version=target_version,
                compatible=True,
                check_type=CompatibilityType.NONE,
            )

        violations: list[str] = []

        if type in (CompatibilityType.BACKWARD, CompatibilityType.FULL):
            violations.extend(self._check_backward(source, target))

        if type in (CompatibilityType.FORWARD, CompatibilityType.FULL):
            violations.extend(self._check_forward(source, target))

        return CompatibilityResult(
            id=result_id,
            schema_id=schema_id,
            source_version=source_version,
            target_version=target_version,
            compatible=len(violations) == 0,
            violations=tuple(violations),
            check_type=type,
        )

    def _check_backward(self, source: SchemaVersion, target: SchemaVersion) -> list[str]:
        violations: list[str] = []
        source_fields = self._extract_fields(source.content)
        target_fields = self._extract_fields(target.content)

        source_names = {f["name"] for f in source_fields}
        target_names = {f["name"] for f in target_fields}

        removed_fields = source_names - target_names
        for f in removed_fields:
            violations.append(
                f"Backward: field {f!r} removed in target (reader cannot read old data)"
            )

        source_required = {f["name"] for f in source_fields if f.get("required", False)}
        target_required = {f["name"] for f in target_fields if f.get("required", False)}
        new_required = target_required - source_required
        for f in new_required:
            violations.append(
                f"Backward: field {f!r} added as required in target (reader expects it)"
            )

        for sf in source_fields:
            for tf in target_fields:
                if sf["name"] == tf["name"]:
                    if not self._types_compatible(tf.get("type", ""), sf.get("type", "")):
                        violations.append(
                            f"Backward: field {sf['name']!r} type changed from {sf.get('type', '')} "
                            f"to {tf.get('type', '')} (reader expects {sf.get('type', '')})"
                        )
                    break

        return violations

    def _check_forward(self, source: SchemaVersion, target: SchemaVersion) -> list[str]:
        violations: list[str] = []
        source_fields = self._extract_fields(source.content)
        target_fields = self._extract_fields(target.content)

        source_names = {f["name"] for f in source_fields}
        target_names = {f["name"] for f in target_fields}

        added_fields = target_names - source_names
        for f in added_fields:
            violations.append(
                f"Forward: field {f!r} added in target (new reader cannot read old data)"
            )

        source_required = {f["name"] for f in source_fields if f.get("required", False)}
        target_required = {f["name"] for f in target_fields if f.get("required", False)}
        removed_required = source_required - target_required
        for f in removed_required:
            violations.append(
                f"Forward: field {f!r} was required but is missing in target (old data lacks it)"
            )

        for sf in source_fields:
            for tf in target_fields:
                if sf["name"] == tf["name"]:
                    if not self._types_compatible(sf.get("type", ""), tf.get("type", "")):
                        violations.append(
                            f"Forward: field {sf['name']!r} type changed from {sf.get('type', '')} "
                            f"to {tf.get('type', '')} (new reader cannot read old data)"
                        )
                    break

        return violations

    def _extract_fields(self, content: str) -> list[dict[str, Any]]:
        try:
            schema = json.loads(content)
        except json.JSONDecodeError:
            return []

        fields: list[dict[str, Any]] = []

        raw_fields = schema.get("fields") or schema.get("properties") or []
        if isinstance(raw_fields, dict):
            for name, props in raw_fields.items():
                field_type = props if isinstance(props, str) else props.get("type", "string")
                required = name in schema.get("required", []) if isinstance(props, dict) else False
                fields.append({"name": name, "type": field_type, "required": required})
        elif isinstance(raw_fields, list):
            for f in raw_fields:
                if isinstance(f, dict):
                    fields.append(f)
                elif isinstance(f, str):
                    fields.append({"name": f, "type": "string", "required": False})

        return fields

    def _types_compatible(self, type_a: str, type_b: str) -> bool:
        type_a = type_a.lower().strip() if isinstance(type_a, str) else "string"
        type_b = type_b.lower().strip() if isinstance(type_b, str) else "string"
        if type_a == type_b:
            return True
        widening = {
            "int": ["long", "double", "float", "string"],
            "long": ["double", "float", "string"],
            "float": ["double"],
            "integer": ["number", "string"],
            "number": ["string"],
        }
        return type_b in widening.get(type_a, [])


__all__ = ["CompatibilityChecker"]
