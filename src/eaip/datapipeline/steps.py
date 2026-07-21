from __future__ import annotations

import asyncio
import copy
from typing import Any

from eaip.datapipeline.exceptions import StepExecutionError
from eaip.datapipeline.models import DataRecord, PipelineStep, StepType
from eaip.logging.context import get_logger
from eaip.shared.sandbox import safe_exec


class StepExecutor:
    def __init__(self) -> None:
        self._log = get_logger("eaip.datapipeline.steps")

    async def execute_transform(
        self,
        step: PipelineStep,
        record: DataRecord,
        context: dict[str, Any],
    ) -> DataRecord:
        mapping = step.config.get("mapping", {})
        transformed_data = {}
        for target_field, source_field in mapping.items():
            if isinstance(source_field, str) and source_field in record.data:
                transformed_data[target_field] = copy.deepcopy(record.data[source_field])
            else:
                transformed_data[target_field] = source_field
        return DataRecord(
            id=record.id,
            data=transformed_data,
            metadata={**record.metadata, "transformed_by": step.id},
            source=record.source,
            timestamp=record.timestamp,
            schema_version=record.schema_version,
            checksum=record.checksum,
        )

    async def execute_filter(
        self,
        step: PipelineStep,
        record: DataRecord,
        context: dict[str, Any],
    ) -> DataRecord | None:
        condition = step.config.get("condition", {})
        field = condition.get("field")
        operator = condition.get("operator", "eq")
        value = condition.get("value")

        if field is None:
            return record

        actual = record.data.get(field)

        if operator == "eq":
            keep = actual == value
        elif operator == "neq":
            keep = actual != value
        elif operator == "gt":
            keep = actual is not None and actual > value
        elif operator == "gte":
            keep = actual is not None and actual >= value
        elif operator == "lt":
            keep = actual is not None and actual < value
        elif operator == "lte":
            keep = actual is not None and actual <= value
        elif operator == "in":
            keep = actual in (value or [])
        elif operator == "exists":
            keep = (actual is not None) == value
        else:
            keep = True

        return record if keep else None

    async def execute_validate(
        self,
        step: PipelineStep,
        record: DataRecord,
        context: dict[str, Any],
    ) -> DataRecord:
        rules = step.config.get("rules", [])
        errors: list[str] = []

        for rule in rules:
            field = rule.get("field")
            rule_type = rule.get("type", "required")

            if rule_type == "required":
                if field not in record.data or record.data[field] is None:
                    errors.append(f"Field '{field}' is required")
            elif rule_type == "type":
                expected = rule.get("expected_type", "str")
                actual_val = record.data.get(field)
                if actual_val is not None and type(actual_val).__name__ != expected:
                    errors.append(
                        f"Field '{field}' expected type '{expected}', got '{type(actual_val).__name__}'",
                    )
            elif rule_type == "range":
                val = record.data.get(field)
                if val is not None:
                    min_val = rule.get("min")
                    max_val = rule.get("max")
                    if min_val is not None and val < min_val:
                        errors.append(f"Field '{field}' is below minimum {min_val}")
                    if max_val is not None and val > max_val:
                        errors.append(f"Field '{field}' is above maximum {max_val}")
            elif rule_type == "pattern":
                import re

                val = record.data.get(field)
                pattern = rule.get("pattern", "")
                if val is not None and not re.match(pattern, str(val)):
                    errors.append(f"Field '{field}' does not match pattern '{pattern}'")

        if errors:
            from eaip.datapipeline.exceptions import DataValidationError

            raise DataValidationError(
                "Validation failed",
                context={"step_id": step.id, "record_id": record.id, "errors": errors},
            )

        return record

    async def execute_enrich(
        self,
        step: PipelineStep,
        record: DataRecord,
        context: dict[str, Any],
    ) -> DataRecord:
        enrichments = step.config.get("enrichments", {})
        enriched_data = {**record.data}

        for target_field, source_config in enrichments.items():
            if isinstance(source_config, str):
                enriched_data[target_field] = context.get(source_config, source_config)
            elif isinstance(source_config, dict):
                default = source_config.get("default")
                source_key = source_config.get("source_key")
                if source_key:
                    enriched_data[target_field] = context.get(source_key, default)
                else:
                    enriched_data[target_field] = source_config.get("value", default)
            else:
                enriched_data[target_field] = source_config

        return DataRecord(
            id=record.id,
            data=enriched_data,
            metadata={**record.metadata, "enriched_by": step.id},
            source=record.source,
            timestamp=record.timestamp,
            schema_version=record.schema_version,
            checksum=record.checksum,
        )

    async def execute_aggregate(
        self,
        step: PipelineStep,
        records: list[DataRecord],
        context: dict[str, Any],
    ) -> list[DataRecord]:
        operation = step.config.get("operation", "collect")
        group_by = step.config.get("group_by")
        target_field = step.config.get("target_field", "aggregated")

        if not records:
            return records

        if operation == "collect":
            aggregated = [r.model_dump() for r in records]
            return [
                DataRecord(
                    id=records[0].id,
                    data={target_field: aggregated, "_count": len(records)},
                    metadata={**records[0].metadata, "aggregated_by": step.id},
                    source=records[0].source,
                    timestamp=records[0].timestamp,
                ),
            ]
        if group_by:
            groups: dict[str, list[DataRecord]] = {}
            for r in records:
                key = str(r.data.get(group_by, "unknown"))
                groups.setdefault(key, []).append(r)

            results = []
            for key, group in groups.items():
                values = [r.data for r in group]
                results.append(
                    DataRecord(
                        id=f"{records[0].id}_{key}",
                        data={target_field: values, "_group": key, "_count": len(group)},
                        metadata={**records[0].metadata, "aggregated_by": step.id},
                        source=records[0].source,
                        timestamp=records[0].timestamp,
                    ),
                )
            return results

        return records

    async def execute_script(
        self,
        step: PipelineStep,
        record: DataRecord,
        context: dict[str, Any],
    ) -> DataRecord:
        script_code = step.config.get("script", "")
        if not script_code:
            return record

        local_context: dict[str, Any] = {
            "record": record.model_copy(deep=True),
            "context": context,
            "data": dict(record.data),
        }

        try:
            safe_exec(script_code, local_scope=local_context)
        except ValueError as exc:
            raise StepExecutionError(
                f"Script rejected by sandbox: {exc}",
                context={"step_id": step.id, "record_id": record.id},
                cause=exc,
            )
        except Exception as exc:
            raise StepExecutionError(
                f"Script execution failed: {exc}",
                context={"step_id": step.id, "record_id": record.id},
                cause=exc,
            )

        result_data = local_context.get("data", record.data)
        return DataRecord(
            id=record.id,
            data=result_data,
            metadata={**record.metadata, "script_executed_by": step.id},
            source=record.source,
            timestamp=record.timestamp,
            schema_version=record.schema_version,
            checksum=record.checksum,
        )

    async def run_step(
        self,
        step: PipelineStep,
        record: DataRecord,
        context: dict[str, Any],
    ) -> DataRecord | None:
        if not step.enabled:
            return record

        retry_policy = step.retry_policy
        max_retries = retry_policy.get("max_retries", 0)
        delay = retry_policy.get("delay_seconds", 1.0)

        for attempt in range(max_retries + 1):
            try:
                if step.type == StepType.TRANSFORM:
                    return await self.execute_transform(step, record, context)
                if step.type == StepType.FILTER:
                    return await self.execute_filter(step, record, context)
                if step.type == StepType.VALIDATE:
                    return await self.execute_validate(step, record, context)
                if step.type == StepType.ENRICH:
                    return await self.execute_enrich(step, record, context)
                if step.type == StepType.SCRIPT:
                    return await self.execute_script(step, record, context)
                return record
            except Exception as exc:
                if attempt < max_retries:
                    self._log.warning(
                        "step.retry",
                        step_id=step.id,
                        attempt=attempt + 1,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)
                    delay *= retry_policy.get("backoff_multiplier", 2.0)
                else:
                    raise StepExecutionError(
                        f"Step {step.id!r} ({step.name}) failed after {max_retries + 1} attempts",
                        context={"step_id": step.id, "attempt": attempt + 1},
                        cause=exc,
                    )

        return record


__all__ = ["StepExecutor"]
