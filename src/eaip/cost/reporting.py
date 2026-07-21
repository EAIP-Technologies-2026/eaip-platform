"""Cost reporting — chargeback, summaries, top cost drivers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from typing import Any

from eaip.cost.models import Category, ChargebackItem, ChargebackReport, CostRecord
from eaip.cost.tracker import CostTracker


class CostReportingService:
    """Generates chargeback reports and cost summaries."""

    def __init__(self, tracker: CostTracker) -> None:
        self._tracker = tracker
        self._reports: dict[str, ChargebackReport] = {}
        self._report_counter: int = 0
        self._event_callback: Callable[..., Any] | None = None

    def set_event_callback(self, callback: Callable[..., Any]) -> None:
        self._event_callback = callback

    async def _emit(self, event: Any) -> None:
        if self._event_callback is not None:
            await self._event_callback(event)

    async def generate_chargeback(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> ChargebackReport:
        records = await self._tracker.query_costs(start=period_start, end=period_end)
        total_cost = sum(r.amount for r in records)

        # group by tenant_id
        tenant_groups: dict[str | None, list[CostRecord]] = defaultdict(list)
        for r in records:
            tenant_groups[r.tenant_id].append(r)

        # group within tenant by category
        tenant_category_totals: dict[str | None, dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        for r in records:
            tenant_category_totals[r.tenant_id][r.category.value] += r.amount

        items: list[ChargebackItem] = []
        for tenant_id, tenant_records in tenant_groups.items():
            if tenant_id is None:
                continue
            tenant_cost = sum(r.amount for r in tenant_records)
            cat_breakdown = dict(tenant_category_totals[tenant_id])
            primary_cat_str = (
                max(cat_breakdown, key=lambda k: cat_breakdown[k]) if cat_breakdown else "other"
            )
            primary_cat = Category(primary_cat_str)

            usage_metrics: dict[str, float] = {}
            for r in tenant_records:
                if r.resource_type:
                    key = f"{r.resource_type}_count"
                    usage_metrics[key] = usage_metrics.get(key, 0) + 1

            percentage = (tenant_cost / total_cost * 100) if total_cost > 0 else 0.0
            items.append(
                ChargebackItem(
                    tenant_id=tenant_id,
                    tenant_name=f"Tenant-{tenant_id}",
                    category=primary_cat,
                    amount=tenant_cost,
                    percentage=percentage,
                    usage_metrics=usage_metrics,
                )
            )

        self._report_counter += 1
        report = ChargebackReport(
            id=f"cb-{self._report_counter}",
            period_start=period_start,
            period_end=period_end,
            total_cost=total_cost,
            items=tuple(items),
            currency="USD",
        )
        self._reports[report.id] = report

        if self._event_callback is not None:
            from eaip.cost.events import ChargebackGenerated

            await self._event_callback(
                ChargebackGenerated(
                    report_id=report.id,
                    period_start=period_start,
                    period_end=period_end,
                    total_cost=total_cost,
                    item_count=len(items),
                )
            )
        return report

    async def get_tenant_cost_summary(
        self,
        tenant_id: str,
        period: tuple[datetime, datetime] | None = None,
    ) -> dict[str, Any]:
        records = await self._tracker.query_costs(tenant_id=tenant_id)
        if period is not None:
            start, end = period
            records = [r for r in records if start <= r.timestamp <= end]
        total = sum(r.amount for r in records)
        category_breakdown: dict[str, float] = defaultdict(float)
        workflow_breakdown: dict[str, float] = defaultdict(float)
        for r in records:
            category_breakdown[r.category.value] += r.amount
            if r.workflow_id:
                workflow_breakdown[r.workflow_id] += r.amount
        return {
            "tenant_id": tenant_id,
            "total_cost": total,
            "record_count": len(records),
            "category_breakdown": dict(category_breakdown),
            "workflow_breakdown": dict(workflow_breakdown),
        }

    async def get_workflow_cost_summary(
        self,
        workflow_id: str,
        period: tuple[datetime, datetime] | None = None,
    ) -> dict[str, Any]:
        records = await self._tracker.query_costs(workflow_id=workflow_id)
        if period is not None:
            start, end = period
            records = [r for r in records if start <= r.timestamp <= end]
        total = sum(r.amount for r in records)
        category_breakdown: dict[str, float] = defaultdict(float)
        agent_breakdown: dict[str, float] = defaultdict(float)
        for r in records:
            category_breakdown[r.category.value] += r.amount
            if r.agent_id:
                agent_breakdown[r.agent_id] += r.amount
        return {
            "workflow_id": workflow_id,
            "total_cost": total,
            "record_count": len(records),
            "category_breakdown": dict(category_breakdown),
            "agent_breakdown": dict(agent_breakdown),
        }

    async def get_top_cost_drivers(
        self,
        scope: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        records = await self._tracker.query_costs()
        groupings: dict[str, float] = defaultdict(float)
        for r in records:
            key = None
            if scope == "tenant" and r.tenant_id:
                key = r.tenant_id
            elif scope == "workflow" and r.workflow_id:
                key = r.workflow_id
            elif scope == "agent" and r.agent_id:
                key = r.agent_id
            elif scope == "resource" and r.resource_id:
                key = f"{r.resource_type}:{r.resource_id}"
            if key:
                groupings[key] += r.amount
        sorted_items = sorted(groupings.items(), key=lambda x: x[1], reverse=True)
        return [
            {"scope": scope, "id": item_id, "cost": cost} for item_id, cost in sorted_items[:limit]
        ]
