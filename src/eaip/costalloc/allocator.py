"""Cost allocation service — allocate costs, manage rules."""

from __future__ import annotations

from typing import Any

from eaip.costalloc.exceptions import RuleNotFoundError
from eaip.costalloc.models import AllocationRule, CostAllocation


class CostAllocationService:
    def __init__(self) -> None:
        self._allocations: list[CostAllocation] = []
        self._rules: list[AllocationRule] = []

    async def allocate_cost(self, allocation: CostAllocation) -> CostAllocation:
        self._allocations.append(allocation)
        return allocation

    async def create_rule(self, rule: AllocationRule) -> AllocationRule:
        self._rules.append(rule)
        return rule

    async def update_rule(self, rule_id: str, updates: dict[str, Any]) -> AllocationRule:
        for i, rule in enumerate(self._rules):
            if rule.id == rule_id:
                updated = rule.model_copy(update=updates)
                self._rules[i] = updated
                return updated
        raise RuleNotFoundError(f"Rule {rule_id} not found")

    async def get_allocation(self, allocation_id: str) -> CostAllocation | None:
        for a in self._allocations:
            if a.id == allocation_id:
                return a
        return None

    async def list_allocations(self) -> list[CostAllocation]:
        return list(self._allocations)

    async def list_rules(self) -> list[AllocationRule]:
        return list(self._rules)

    async def get_rule(self, rule_id: str) -> AllocationRule | None:
        for r in self._rules:
            if r.id == rule_id:
                return r
        return None
