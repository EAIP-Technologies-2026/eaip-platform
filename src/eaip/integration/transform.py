"""MessageTransformationService — apply mapping, filter, enrich, and script transforms."""

from __future__ import annotations

from typing import Any

from eaip.integration.exceptions import TransformationError
from eaip.integration.models import IntegrationMessage, Transformation
from eaip.logging.context import get_logger
from eaip.shared.sandbox import safe_exec


class MessageTransformationService:
    def __init__(self) -> None:
        self._transformations: dict[str, Transformation] = {}
        self._log = get_logger("eaip.integration.transform")

    def register_transformation(self, transform: Transformation) -> None:
        self._transformations[transform.id] = transform

    async def transform(
        self, message: IntegrationMessage, transformation_ids: tuple[str, ...]
    ) -> IntegrationMessage:
        current = message
        for tid in transformation_ids:
            transform = self._transformations.get(tid)
            if transform is None:
                raise TransformationError(
                    f"Transformation {tid!r} not found",
                    context={"transformation_id": tid},
                )
            if not transform.enabled:
                self._log.warning("integration.transform.disabled", transformation_id=tid)
                continue

            if transform.type == "mapping":
                current = await self.apply_mapping(current, transform.config)
            elif transform.type == "filter":
                current = await self.apply_filter(current, transform.config)
            elif transform.type == "enrich":
                current = await self.apply_enrichment(current, transform.config)
            elif transform.type == "script":
                current = await self.apply_script_transform(current, transform.config)
            else:
                raise TransformationError(
                    f"Unknown transformation type {transform.type!r}",
                    context={"transformation_id": tid, "type": transform.type},
                )
        return current

    async def apply_mapping(
        self, message: IntegrationMessage, config: dict[str, Any]
    ) -> IntegrationMessage:
        mapping = config.get("field_mapping", {})
        new_payload = dict(message.payload)
        for source_field, target_field in mapping.items():
            if source_field in new_payload:
                new_payload[target_field] = new_payload.pop(source_field)
        return message.model_copy(update={"payload": new_payload})

    async def apply_filter(
        self, message: IntegrationMessage, config: dict[str, Any]
    ) -> IntegrationMessage:
        field = config.get("field")
        operator = config.get("operator", "eq")
        value = config.get("value")

        actual = message.payload.get(field) if field else None

        if (operator == "eq" and actual == value) or (operator == "neq" and actual != value):
            return message
        if (
            (operator == "exists" and field in message.payload)
            or (
                operator == "gt"
                and isinstance(actual, (int, float))
                and isinstance(value, (int, float))
                and actual > value
            )
            or (
                operator == "gte"
                and isinstance(actual, (int, float))
                and isinstance(value, (int, float))
                and actual >= value
            )
            or (
                operator == "lt"
                and isinstance(actual, (int, float))
                and isinstance(value, (int, float))
                and actual < value
            )
            or (
                operator == "lte"
                and isinstance(actual, (int, float))
                and isinstance(value, (int, float))
                and actual <= value
            )
        ):
            return message

        new_payload = {"_filtered": True, "_reason": f"Field {field} did not match condition"}
        return message.model_copy(update={"payload": new_payload})

    async def apply_enrichment(
        self, message: IntegrationMessage, config: dict[str, Any]
    ) -> IntegrationMessage:
        enrichment_data = config.get("data", {})
        new_payload = {**message.payload, **enrichment_data}
        return message.model_copy(update={"payload": new_payload})

    async def apply_script_transform(
        self, message: IntegrationMessage, config: dict[str, Any]
    ) -> IntegrationMessage:
        script_source = config.get("script", "")
        if not script_source:
            return message
        try:
            local_vars: dict[str, Any] = {
                "payload": dict(message.payload),
                "headers": dict(message.headers),
            }
            safe_exec(script_source, local_scope=local_vars)
            result = local_vars.get("result", local_vars.get("payload", message.payload))
            return message.model_copy(update={"payload": result})
        except ValueError as exc:
            raise TransformationError(
                f"Script rejected by sandbox: {exc}",
                context={"transformation_id": config.get("id", "unknown")},
                cause=exc,
            )
        except Exception as exc:
            raise TransformationError(
                f"Script transformation failed: {exc}",
                context={"transformation_id": config.get("id", "unknown")},
                cause=exc,
            )


__all__ = ["MessageTransformationService"]
