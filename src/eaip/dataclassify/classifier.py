"""Data classifier service — CRUD for rules and classification logic."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.dataclassify.events import (
    ClassificationPerformed,
    ClassificationRuleCreated,
    ClassificationRuleUpdated,
)
from eaip.dataclassify.exceptions import ClassNotFoundError
from eaip.dataclassify.models import (
    ClassificationResult,
    ClassifierConfig,
    DataClass,
)
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now

logger = get_logger("eaip.dataclassify.classifier")


class DataClassifier:
    def __init__(
        self,
        config: ClassifierConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config = config or ClassifierConfig()
        self._event_bus = event_bus or EventBus()
        self._rules: dict[str, DataClass] = {}
        self._results: dict[str, ClassificationResult] = {}

    @property
    def config(self) -> ClassifierConfig:
        return self._config

    async def create_rule(self, rule: DataClass) -> DataClass:
        self._rules[rule.id] = rule
        await self._event_bus.publish(
            ClassificationRuleCreated(
                rule_id=rule.id,
                rule_name=rule.name,
                category=rule.category.value,
            )
        )
        return rule

    async def get_rule(self, rule_id: str) -> DataClass:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise ClassNotFoundError(f"Classification rule '{rule_id}' not found")
        return rule

    async def update_rule(self, rule_id: str, **updates: Any) -> DataClass:
        existing = await self.get_rule(rule_id)
        changes = {k: v for k, v in updates.items() if getattr(existing, k, None) != v}
        updated = existing.model_copy(update=updates)
        self._rules[rule_id] = updated
        await self._event_bus.publish(
            ClassificationRuleUpdated(
                rule_id=rule_id,
                rule_name=updated.name,
                changes=changes,
            )
        )
        return updated

    async def delete_rule(self, rule_id: str) -> None:
        if rule_id not in self._rules:
            raise ClassNotFoundError(f"Classification rule '{rule_id}' not found")
        del self._rules[rule_id]

    async def list_rules(self) -> tuple[DataClass, ...]:
        return tuple(self._rules.values())

    async def classify(
        self,
        resource_id: str,
        patterns_found: tuple[str, ...],
    ) -> ClassificationResult:
        matched: list[str] = []
        highest_priority = -1
        for rule in self._rules.values():
            if not rule.pattern:
                continue
            for pf in patterns_found:
                if rule.pattern.lower() in pf.lower() or pf.lower() in rule.pattern.lower():
                    highest_priority = max(highest_priority, rule.priority)
                    if rule.name not in matched:
                        matched.append(rule.name)

        confidence = min(len(matched) / max(len(self._rules), 1), 1.0) if self._rules else 0.0
        result = ClassificationResult(
            id=str(uuid.uuid4()),
            resource_id=resource_id,
            detected_classes=tuple(matched),
            confidence=confidence,
            classified_at=utc_now(),
        )
        self._results[result.id] = result
        await self._event_bus.publish(
            ClassificationPerformed(
                resource_id=resource_id,
                classes_found=result.detected_classes,
                confidence=result.confidence,
            )
        )
        return result

    async def get_result(self, result_id: str) -> ClassificationResult:
        result = self._results.get(result_id)
        if result is None:
            raise ClassNotFoundError(f"Classification result '{result_id}' not found")
        return result
