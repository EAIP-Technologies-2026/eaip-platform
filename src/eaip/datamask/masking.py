"""Data masking service — CRUD for rules, apply masking strategies."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from cryptography.fernet import Fernet

from eaip.datamask.events import MaskingRuleCreated, MaskingRuleUpdated
from eaip.datamask.exceptions import MaskingRuleNotFoundError
from eaip.datamask.models import MaskingConfig, MaskingRule, MaskingStrategy
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger

logger = get_logger("eaip.datamask.masking")


class DataMaskingService:
    def __init__(
        self,
        config: MaskingConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config = config or MaskingConfig()
        self._event_bus = event_bus or EventBus()
        self._rules: dict[str, MaskingRule] = {}

    @property
    def config(self) -> MaskingConfig:
        return self._config

    async def create_rule(self, rule: MaskingRule) -> MaskingRule:
        self._rules[rule.id] = rule
        await self._event_bus.publish(
            MaskingRuleCreated(
                rule_id=rule.id,
                rule_name=rule.name,
                data_type=rule.data_type.value,
                strategy=rule.strategy.value,
            )
        )
        return rule

    async def get_rule(self, rule_id: str) -> MaskingRule:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise MaskingRuleNotFoundError(f"Masking rule '{rule_id}' not found")
        return rule

    async def update_rule(self, rule_id: str, **updates: Any) -> MaskingRule:
        existing = await self.get_rule(rule_id)
        changes = {k: v for k, v in updates.items() if getattr(existing, k, None) != v}
        updated = existing.model_copy(update=updates)
        self._rules[rule_id] = updated
        await self._event_bus.publish(
            MaskingRuleUpdated(
                rule_id=rule_id,
                rule_name=updated.name,
                changes=changes,
            )
        )
        return updated

    async def delete_rule(self, rule_id: str) -> None:
        if rule_id not in self._rules:
            raise MaskingRuleNotFoundError(f"Masking rule '{rule_id}' not found")
        del self._rules[rule_id]

    async def list_rules(self) -> tuple[MaskingRule, ...]:
        return tuple(self._rules.values())

    async def apply_masking(
        self,
        data: Mapping[str, Any],
        rules: tuple[MaskingRule, ...],
    ) -> dict[str, Any]:
        masked: dict[str, Any] = {}
        for key, value in data.items():
            matched = False
            for rule in rules:
                if not rule.enabled:
                    continue
                if self._field_matches_pattern(key, rule.field_pattern):
                    masked[key] = await self.mask_field(value, rule.strategy, rule)
                    matched = True
                    break
            if not matched:
                masked[key] = deepcopy(value)
        return masked

    async def mask_field(
        self,
        value: Any,
        strategy: MaskingStrategy,
        config: MaskingRule,
    ) -> Any:
        if not isinstance(value, str):
            return value

        if strategy is MaskingStrategy.MASK:
            return self._apply_mask(value, config)
        if strategy is MaskingStrategy.TRUNCATE:
            return self._apply_truncate(value, config)
        if strategy is MaskingStrategy.HASH:
            return self._apply_hash(value)
        if strategy is MaskingStrategy.REDACT:
            return self._apply_redact(value)
        if strategy is MaskingStrategy.ENCRYPT:
            return await self._apply_encrypt(value, config)
        if strategy is MaskingStrategy.SUBSTITUTE:
            return self._apply_substitute(value, config)
        return value  # type: ignore[unreachable]

    def _field_matches_pattern(self, field_name: str, pattern: str) -> bool:
        import fnmatch

        return fnmatch.fnmatch(field_name.lower(), pattern.lower())

    def _apply_mask(self, value: str, config: MaskingRule) -> str:
        char = config.mask_character
        if config.preserve_prefix_count and config.preserve_prefix_count < len(value):
            prefix = value[: config.preserve_prefix_count]
            rest_len = len(value) - config.preserve_prefix_count
            if config.preserve_length:
                return prefix + char * rest_len
            return prefix + char * min(rest_len, 4)
        if config.preserve_length:
            return char * len(value)
        return char * 4

    def _apply_truncate(self, value: str, config: MaskingRule) -> str:
        count = config.preserve_prefix_count or 10
        return value[:count]

    def _apply_hash(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _apply_redact(self, value: str) -> str:
        return f"[REDACTED {len(value)} chars]"

    async def _apply_encrypt(self, value: str, config: MaskingRule) -> str:
        key = config.metadata.get("encryption_key")
        if key:
            f = Fernet(key.encode("utf-8") if isinstance(key, str) else key)
        else:
            f = Fernet(Fernet.generate_key())
        return f.encrypt(value.encode("utf-8")).decode("utf-8")

    def _apply_substitute(self, value: str, config: MaskingRule) -> str:
        return config.substitution_dict.get(value, value)
