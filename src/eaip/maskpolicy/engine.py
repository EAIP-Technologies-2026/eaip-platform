"""Masking policy engine — CRUD for policies and rules, apply logic."""

from __future__ import annotations

from typing import Any

from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.maskpolicy.events import PolicyApplied, PolicyCreated, PolicyUpdated
from eaip.maskpolicy.exceptions import PolicyNotFoundError
from eaip.maskpolicy.models import MaskingConfig, MaskingPolicy, PolicyStatus

logger = get_logger("eaip.maskpolicy.engine")


class MaskingPolicyEngine:
    def __init__(
        self,
        config: MaskingConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config = config or MaskingConfig()
        self._event_bus = event_bus or EventBus()
        self._policies: dict[str, MaskingPolicy] = {}

    @property
    def config(self) -> MaskingConfig:
        return self._config

    async def create_policy(self, policy: MaskingPolicy) -> MaskingPolicy:
        self._policies[policy.id] = policy
        await self._event_bus.publish(
            PolicyCreated(
                policy_id=policy.id,
                policy_name=policy.name,
                environment=policy.environment,
            )
        )
        return policy

    async def get_policy(self, policy_id: str) -> MaskingPolicy:
        policy = self._policies.get(policy_id)
        if policy is None:
            raise PolicyNotFoundError(f"Masking policy '{policy_id}' not found")
        return policy

    async def update_policy(self, policy_id: str, **updates: Any) -> MaskingPolicy:
        existing = await self.get_policy(policy_id)
        changes = {k: v for k, v in updates.items() if getattr(existing, k, None) != v}
        updated = existing.model_copy(update=updates)
        self._policies[policy_id] = updated
        await self._event_bus.publish(
            PolicyUpdated(
                policy_id=policy_id,
                policy_name=updated.name,
                changes=changes,
            )
        )
        return updated

    async def delete_policy(self, policy_id: str) -> None:
        if policy_id not in self._policies:
            raise PolicyNotFoundError(f"Masking policy '{policy_id}' not found")
        del self._policies[policy_id]

    async def list_policies(self, status: PolicyStatus | None = None) -> tuple[MaskingPolicy, ...]:
        policies = list(self._policies.values())
        if status is not None:
            policies = [p for p in policies if p.status is status]
        return tuple(policies)

    async def apply_policy(self, policy_id: str) -> MaskingPolicy:
        policy = await self.get_policy(policy_id)
        if policy.status is not PolicyStatus.ACTIVE:
            activated = policy.model_copy(update={"status": PolicyStatus.ACTIVE})
            self._policies[policy_id] = activated
            policy = activated
        await self._event_bus.publish(
            PolicyApplied(
                policy_id=policy.id,
                policy_name=policy.name,
                rules_applied=len(policy.rules),
            )
        )
        return policy

    async def archive_policy(self, policy_id: str) -> MaskingPolicy:
        policy = await self.get_policy(policy_id)
        archived = policy.model_copy(update={"status": PolicyStatus.ARCHIVED})
        self._policies[policy_id] = archived
        return archived
