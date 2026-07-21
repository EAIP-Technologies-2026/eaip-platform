"""Audit policy service — create, manage, evaluate, and enforce retention policies."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from eaip.audit.exceptions import PolicyNotFoundError
from eaip.audit.models import AuditEvent, AuditPolicy, RetentionRule
from eaip.logging.context import get_logger


class AuditPolicyService:
    def __init__(self) -> None:
        self._policies: dict[str, AuditPolicy] = {}
        self._retention_rules: dict[str, RetentionRule] = {}
        self._log = get_logger("eaip.audit.policies")

    def create_policy(self, policy: AuditPolicy) -> AuditPolicy:
        self._policies[policy.id] = policy
        self._log.info("audit.policy.created", policy_id=policy.id, name=policy.name)
        return policy

    def get_policy(self, policy_id: str) -> AuditPolicy:
        policy = self._policies.get(policy_id)
        if policy is None:
            raise PolicyNotFoundError(f"Audit policy {policy_id!r} not found")
        return policy

    def update_policy(self, policy_id: str, **updates: Any) -> AuditPolicy:
        existing = self.get_policy(policy_id)
        updated = existing.model_copy(update=updates)
        self._policies[policy_id] = updated
        self._log.info("audit.policy.updated", policy_id=policy_id)
        return updated

    def delete_policy(self, policy_id: str) -> None:
        if policy_id not in self._policies:
            raise PolicyNotFoundError(f"Audit policy {policy_id!r} not found")
        del self._policies[policy_id]
        self._log.info("audit.policy.deleted", policy_id=policy_id)

    def list_policies(self) -> list[AuditPolicy]:
        return list(self._policies.values())

    async def evaluate_policy(self, event: AuditEvent) -> list[str]:
        actions: list[str] = []
        for policy in self._policies.values():
            if not policy.enabled:
                continue
            if policy.event_types and event.event_type not in policy.event_types:
                continue
            if event.event_type in policy.notify_on_events:
                actions.append(f"notify:{policy.name}")
        return actions

    def add_retention_rule(self, rule: RetentionRule) -> RetentionRule:
        self._retention_rules[rule.id] = rule
        self._log.info("audit.retention.rule.added", rule_id=rule.id, data_type=rule.data_type)
        return rule

    async def check_retention(self, data_type: str) -> int:
        matching = [
            r for r in self._retention_rules.values() if r.data_type == data_type and r.enabled
        ]
        if not matching:
            return 90
        return max(r.retention_period_days for r in matching)

    async def apply_retention(self) -> dict[str, int]:
        datetime.now(UTC)
        results: dict[str, int] = {}
        for rule in self._retention_rules.values():
            if not rule.enabled:
                continue
            if rule.legal_hold_ids:
                continue
            results[rule.id] = 0
        self._log.info("audit.retention.applied", rules_processed=len(results))
        return results


__all__ = ["AuditPolicyService"]
