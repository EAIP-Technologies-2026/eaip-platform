"""Domain events for the cost allocation service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class CostAllocated(DomainEvent):
    event_type: ClassVar[str] = "eaip.costalloc.allocated"

    allocation_id: str
    tenant_id: str
    amount: float
    currency: str
    period_start: datetime
    period_end: datetime


class AllocationRuleCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.costalloc.rule.created"

    rule_id: str
    name: str
    dimension: str
    percentage: float
    criteria: dict[str, Any] = Field(default_factory=dict)


class AllocationRuleUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.costalloc.rule.updated"

    rule_id: str
    updates: dict[str, Any] = Field(default_factory=dict)
