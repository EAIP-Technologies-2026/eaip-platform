"""Cost tracker — record and query cost data in-memory."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from eaip.cost.models import Category, CostRecord


class CostTracker:
    """In-memory cost tracking with filtering and aggregation."""

    def __init__(self) -> None:
        self._records: list[CostRecord] = []
        self._event_callback: Callable[..., Any] | None = None

    def set_event_callback(self, callback: Callable[..., Any]) -> None:
        self._event_callback = callback

    async def record_cost(self, record: CostRecord) -> None:
        self._records.append(record)
        if self._event_callback is not None:
            await self._event_callback(record)

    async def query_costs(
        self,
        *,
        tenant_id: str | None = None,
        workflow_id: str | None = None,
        agent_id: str | None = None,
        category: Category | str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[CostRecord]:
        results = list(self._records)
        if tenant_id is not None:
            results = [r for r in results if r.tenant_id == tenant_id]
        if workflow_id is not None:
            results = [r for r in results if r.workflow_id == workflow_id]
        if agent_id is not None:
            results = [r for r in results if r.agent_id == agent_id]
        if category is not None:
            cat = Category(category) if isinstance(category, str) else category
            results = [r for r in results if r.category == cat]
        if start is not None:
            results = [r for r in results if r.timestamp >= start]
        if end is not None:
            results = [r for r in results if r.timestamp <= end]
        return results

    async def get_total_cost(
        self,
        scope: str,
        scope_id: str | None = None,
        period: tuple[datetime, datetime] | None = None,
    ) -> float:
        results = list(self._records)
        if scope == "tenant" and scope_id is not None:
            results = [r for r in results if r.tenant_id == scope_id]
        elif scope == "workflow" and scope_id is not None:
            results = [r for r in results if r.workflow_id == scope_id]
        elif scope == "agent" and scope_id is not None:
            results = [r for r in results if r.agent_id == scope_id]
        if period is not None:
            start, end = period
            results = [r for r in results if start <= r.timestamp <= end]
        return sum(r.amount for r in results)

    async def get_cost_by_category(
        self,
        tenant_id: str | None = None,
        period: tuple[datetime, datetime] | None = None,
    ) -> dict[str, float]:
        results = list(self._records)
        if tenant_id is not None:
            results = [r for r in results if r.tenant_id == tenant_id]
        if period is not None:
            start, end = period
            results = [r for r in results if start <= r.timestamp <= end]
        breakdown: dict[str, float] = defaultdict(float)
        for r in results:
            breakdown[r.category.value] += r.amount
        return dict(breakdown)

    async def get_cost_trend(
        self,
        scope: str,
        scope_id: str | None = None,
        interval: timedelta | None = None,
    ) -> list[dict[str, Any]]:
        if interval is None:
            interval = timedelta(hours=1)
        results = list(self._records)
        if scope == "tenant" and scope_id is not None:
            results = [r for r in results if r.tenant_id == scope_id]
        elif scope == "workflow" and scope_id is not None:
            results = [r for r in results if r.workflow_id == scope_id]
        elif scope == "agent" and scope_id is not None:
            results = [r for r in results if r.agent_id == scope_id]
        if not results:
            return []
        min_time = min(r.timestamp for r in results)
        max_time = max(r.timestamp for r in results)
        buckets: list[dict[str, Any]] = []
        cursor = min_time
        while cursor <= max_time:
            bucket_end = cursor + interval
            bucket_cost = sum(r.amount for r in results if cursor <= r.timestamp < bucket_end)
            buckets.append(
                {
                    "period_start": cursor,
                    "period_end": bucket_end,
                    "cost": bucket_cost,
                }
            )
            cursor = bucket_end
        return buckets
