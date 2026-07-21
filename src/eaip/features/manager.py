"""Feature flag manager — create, read, update, delete, and evaluate flags."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Any

from eaip.features.events import (
    FlagCreated,
    FlagDisabled,
    FlagEnabled,
    FlagRolloutChanged,
    FlagUpdated,
)
from eaip.features.exceptions import FlagNotFoundError
from eaip.features.models import FeatureFlag, TargetingRule
from eaip.shared.time import utc_now

EventCallback = Callable[[Any], Any]


def _stable_hash(key: str, entity_id: str) -> int:
    """Return a hash integer in [0, 100) for consistent rollout bucketing."""
    raw = f"{key}:{entity_id}".encode()
    return int(hashlib.sha256(raw).hexdigest(), 16) % 100


class FeatureManager:
    """Manages feature flag lifecycle and evaluation."""

    def __init__(self, event_callback: EventCallback | None = None) -> None:
        self._flags: dict[str, FeatureFlag] = {}
        self._event_callback = event_callback

    def set_event_callback(self, callback: EventCallback | None) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback:
            self._event_callback(event)

    async def create_flag(
        self,
        id: str,
        name: str,
        key: str,
        description: str = "",
        enabled: bool = False,
        rollout_percentage: int = 0,
        targeting_rules: tuple[TargetingRule, ...] = (),
        variants: dict[str, str] | None = None,
        tags: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> FeatureFlag:
        now = utc_now()
        flag = FeatureFlag(
            id=id,
            name=name,
            key=key,
            description=description,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            targeting_rules=targeting_rules,
            variants=variants or {},
            tags=tags,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )
        self._flags[id] = flag
        self._emit(
            FlagCreated(
                flag_id=id,
                key=key,
                name=name,
                enabled=enabled,
                tags=tags,
            )
        )
        return flag

    async def get_flag(self, flag_id: str) -> FeatureFlag:
        if flag_id not in self._flags:
            raise FlagNotFoundError(f"Flag not found: {flag_id}", context={"flag_id": flag_id})
        return self._flags[flag_id]

    async def update_flag(
        self,
        flag_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        enabled: bool | None = None,
        rollout_percentage: int | None = None,
        targeting_rules: tuple[TargetingRule, ...] | None = None,
        variants: dict[str, str] | None = None,
        tags: tuple[str, ...] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FeatureFlag:
        flag = await self.get_flag(flag_id)
        changes: dict[str, Any] = {}
        new_enabled = flag.enabled
        new_rollout = flag.rollout_percentage

        if name is not None:
            changes["name"] = name
        if description is not None:
            changes["description"] = description
        if enabled is not None:
            changes["enabled"] = enabled
            new_enabled = enabled
        if rollout_percentage is not None:
            changes["rollout_percentage"] = rollout_percentage
            new_rollout = rollout_percentage
        if targeting_rules is not None:
            changes["targeting_rules"] = [r.model_dump() for r in targeting_rules]
        if variants is not None:
            changes["variants"] = variants
        if tags is not None:
            changes["tags"] = list(tags)
        if metadata is not None:
            changes["metadata"] = metadata

        updated = FeatureFlag(
            id=flag.id,
            name=name or flag.name,
            key=flag.key,
            description=description if description is not None else flag.description,
            enabled=new_enabled,
            rollout_percentage=new_rollout,
            targeting_rules=(
                targeting_rules if targeting_rules is not None else flag.targeting_rules
            ),
            variants=variants if variants is not None else flag.variants,
            tags=tags if tags is not None else flag.tags,
            metadata=metadata if metadata is not None else flag.metadata,
            created_at=flag.created_at,
            updated_at=utc_now(),
        )
        self._flags[flag_id] = updated
        self._emit(FlagUpdated(flag_id=flag_id, key=flag.key, changes=changes))

        if enabled is True and not flag.enabled:
            self._emit(FlagEnabled(flag_id=flag_id, key=flag.key, rollout_percentage=new_rollout))
        elif enabled is False and flag.enabled:
            self._emit(FlagDisabled(flag_id=flag_id, key=flag.key))

        if rollout_percentage is not None and rollout_percentage != flag.rollout_percentage:
            self._emit(
                FlagRolloutChanged(
                    flag_id=flag_id,
                    key=flag.key,
                    previous_percentage=flag.rollout_percentage,
                    new_percentage=rollout_percentage,
                )
            )

        return updated

    async def delete_flag(self, flag_id: str) -> None:
        if flag_id not in self._flags:
            raise FlagNotFoundError(f"Flag not found: {flag_id}", context={"flag_id": flag_id})
        del self._flags[flag_id]

    async def list_flags(self) -> list[FeatureFlag]:
        return list(self._flags.values())

    async def is_enabled(self, flag_id: str, entity_id: str | None = None) -> bool:
        """Evaluate whether a flag is enabled for a given entity.

        Checks: enabled flag, rollout percentage bucketing, and targeting rules.
        """
        flag = await self.get_flag(flag_id)
        if not flag.enabled:
            return False

        if entity_id is None:
            return False

        if await self._matches_targeting(flag.targeting_rules, entity_id):
            return True

        if flag.rollout_percentage >= 100:
            return True

        if flag.rollout_percentage <= 0:
            return False

        bucket = _stable_hash(flag.key, entity_id)
        return bucket < flag.rollout_percentage

    async def get_flag_value(self, flag_id: str, entity_id: str | None = None) -> str | None:
        """Return the variant value for a flag if enabled, or None."""
        flag = await self.get_flag(flag_id)
        if not await self.is_enabled(flag_id, entity_id):
            return None
        if not flag.variants:
            return "on"
        bucket = _stable_hash(flag.key, entity_id or "") if entity_id else 0
        variant_keys = sorted(flag.variants)
        idx = bucket % len(variant_keys) if len(variant_keys) > 0 else 0
        chosen = variant_keys[idx]
        return flag.variants[chosen]

    async def evaluate_targeting_rules(self, flag_id: str, entity_id: str) -> bool:
        """Check if an entity matches any targeting rule for the flag."""
        flag = await self.get_flag(flag_id)
        return await self._matches_targeting(flag.targeting_rules, entity_id)

    async def _matches_targeting(self, rules: tuple[TargetingRule, ...], entity_id: str) -> bool:
        if not rules:
            return False
        for rule in rules:
            if await self._evaluate_rule(rule, entity_id):
                return True
        return False

    async def _evaluate_rule(self, rule: TargetingRule, value: str) -> bool:
        op = rule.operator
        vals = rule.values
        if op == "in":
            return value in vals
        if op == "not_in":
            return value not in vals
        if op == "contains":
            return any(v in value for v in vals)
        if op == "eq":
            return value == vals[0] if vals else False
        if op == "neq":
            return value != vals[0] if vals else True
        try:
            numeric_val = float(value)
            if op == "gt":
                return any(numeric_val > float(v) for v in vals)
            if op == "gte":
                return any(numeric_val >= float(v) for v in vals)
            if op == "lt":
                return any(numeric_val < float(v) for v in vals)
            if op == "lte":
                return any(numeric_val <= float(v) for v in vals)
        except (ValueError, TypeError):
            pass
        return False

    async def list_flags_by_tags(self, tags: set[str]) -> list[FeatureFlag]:
        return [f for f in self._flags.values() if set(f.tags) & tags]


__all__ = ["FeatureManager"]
