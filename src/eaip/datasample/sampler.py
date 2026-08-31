"""Data sampling service — CRUD for definitions and execution."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.datasample.events import SampleCreated, SampleDefinitionUpdated, SampleExecuted
from eaip.datasample.exceptions import DefinitionNotFoundError
from eaip.datasample.models import (
    SampleDefinition,
    SampleResult,
    SampleStatus,
    SamplingConfig,
)
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now

logger = get_logger("eaip.datasample.sampler")


class DataSamplingService:
    def __init__(
        self,
        config: SamplingConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config = config or SamplingConfig()
        self._event_bus = event_bus or EventBus()
        self._definitions: dict[str, SampleDefinition] = {}
        self._results: dict[str, SampleResult] = {}

    @property
    def config(self) -> SamplingConfig:
        return self._config

    async def create_definition(self, definition: SampleDefinition) -> SampleDefinition:
        self._definitions[definition.id] = definition
        await self._event_bus.publish(
            SampleCreated(
                definition_id=definition.id,
                definition_name=definition.name,
                strategy=definition.strategy.value,
            )
        )
        return definition

    async def get_definition(self, definition_id: str) -> SampleDefinition:
        definition = self._definitions.get(definition_id)
        if definition is None:
            raise DefinitionNotFoundError(f"Sample definition '{definition_id}' not found")
        return definition

    async def update_definition(self, definition_id: str, **updates: Any) -> SampleDefinition:
        existing = await self.get_definition(definition_id)
        changes = {k: v for k, v in updates.items() if getattr(existing, k, None) != v}
        updated = existing.model_copy(update=updates)
        self._definitions[definition_id] = updated
        await self._event_bus.publish(
            SampleDefinitionUpdated(
                definition_id=definition_id,
                definition_name=updated.name,
                changes=changes,
            )
        )
        return updated

    async def delete_definition(self, definition_id: str) -> None:
        if definition_id not in self._definitions:
            raise DefinitionNotFoundError(f"Sample definition '{definition_id}' not found")
        del self._definitions[definition_id]

    async def list_definitions(self, enabled_only: bool = False) -> tuple[SampleDefinition, ...]:
        definitions = list(self._definitions.values())
        if enabled_only:
            definitions = [d for d in definitions if d.enabled]
        return tuple(definitions)

    async def execute_sample(self, definition_id: str) -> SampleResult:
        definition = await self.get_definition(definition_id)
        total = 1000
        sampled = min(definition.sample_size, total)
        result = SampleResult(
            id=str(uuid.uuid4()),
            definition_id=definition_id,
            sampled_records=sampled,
            total_records=total,
            sampled_at=utc_now(),
            status=SampleStatus.COMPLETED,
        )
        self._results[result.id] = result
        await self._event_bus.publish(
            SampleExecuted(
                definition_id=definition_id,
                sampled_records=result.sampled_records,
                total_records=result.total_records,
            )
        )
        return result

    async def get_result(self, result_id: str) -> SampleResult:
        result = self._results.get(result_id)
        if result is None:
            raise DefinitionNotFoundError(f"Sample result '{result_id}' not found")
        return result
