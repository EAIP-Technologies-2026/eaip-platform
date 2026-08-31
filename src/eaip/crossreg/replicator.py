"""Cross-region replicator — manage replication rules and status."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eaip.crossreg.exceptions import RuleNotFoundError
from eaip.crossreg.models import ReplicationRule, ReplicationStatus


class CrossRegionReplicator:
    def __init__(self) -> None:
        self._rules: list[ReplicationRule] = []
        self._statuses: dict[str, ReplicationStatus] = {}

    async def start_replication(self, rule_id: str) -> ReplicationStatus:
        for rule in self._rules:
            if rule.id == rule_id:
                status = ReplicationStatus(
                    rule_id=rule_id,
                    last_sync_at=datetime.now(),
                    items_synced=0,
                    items_failed=0,
                    status="running",
                )
                self._statuses[rule_id] = status
                return status
        raise RuleNotFoundError(f"Replication rule {rule_id} not found")

    async def get_status(self, rule_id: str) -> ReplicationStatus | None:
        return self._statuses.get(rule_id)

    async def list_statuses(self) -> list[ReplicationStatus]:
        return list(self._statuses.values())

    async def list_rules(self) -> list[ReplicationRule]:
        return list(self._rules)

    async def get_rule(self, rule_id: str) -> ReplicationRule | None:
        for r in self._rules:
            if r.id == rule_id:
                return r
        return None

    async def create_rule(self, rule: ReplicationRule) -> ReplicationRule:
        self._rules.append(rule)
        return rule

    async def update_rule(self, rule_id: str, updates: dict[str, Any]) -> ReplicationRule:
        for i, rule in enumerate(self._rules):
            if rule.id == rule_id:
                updated = rule.model_copy(update=updates)
                self._rules[i] = updated
                return updated
        raise RuleNotFoundError(f"Replication rule {rule_id} not found")
