"""MeteringService — record, query, and aggregate usage metrics."""

from __future__ import annotations

from typing import Any

from eaip.logging.context import get_logger
from eaip.metering.events import (
    AggregateComputed,
    UsageRecorded,
)
from eaip.metering.exceptions import MetricNotFoundError
from eaip.metering.models import (
    MeteringConfig,
    MeteringRecord,
    UsageAggregate,
    UsagePeriod,
)


class MeteringService:
    def __init__(self, config: MeteringConfig | None = None) -> None:
        self._config = config or MeteringConfig()
        self._records: dict[str, MeteringRecord] = {}
        self._aggregates: list[UsageAggregate] = []
        self._log = get_logger("eaip.metering.service")

    @property
    def config(self) -> MeteringConfig:
        return self._config

    async def record_usage(self, record: MeteringRecord) -> MeteringRecord:
        self._records[record.id] = record
        UsageRecorded(
            record_id=record.id,
            tenant_id=record.tenant_id,
            metric_name=record.metric_name,
            metric_value=record.metric_value,
        )
        self._log.info(
            "metering.usage.recorded",
            record_id=record.id,
            metric=record.metric_name,
            value=record.metric_value,
        )
        return record

    async def query_usage(
        self,
        tenant_id: str,
        metric_name: str,
        start: Any = None,
        end: Any = None,
    ) -> list[MeteringRecord]:
        results: list[MeteringRecord] = []
        for rec in self._records.values():
            if rec.tenant_id != tenant_id or rec.metric_name != metric_name:
                continue
            if start is not None and rec.timestamp < start:
                continue
            if end is not None and rec.timestamp > end:
                continue
            results.append(rec)
        return results

    async def aggregate(
        self,
        metric_name: str,
        tenant_id: str,
        period: UsagePeriod = UsagePeriod.DAILY,
    ) -> UsageAggregate:
        records = [
            r
            for r in self._records.values()
            if r.tenant_id == tenant_id and r.metric_name == metric_name
        ]
        if not records:
            raise MetricNotFoundError(
                f"No records for metric '{metric_name}' on tenant '{tenant_id}'"
            )

        total_value = sum(r.metric_value for r in records)
        count = len(records)
        avg_value = total_value / count if count > 0 else 0.0
        min_value = min(r.metric_value for r in records)
        max_value = max(r.metric_value for r in records)
        period_start = min(r.timestamp for r in records)
        period_end = max(r.timestamp for r in records)

        aggregate = UsageAggregate(
            metric_name=metric_name,
            tenant_id=tenant_id,
            period=period,
            total_value=total_value,
            count=count,
            average_value=avg_value,
            min_value=min_value,
            max_value=max_value,
            period_start=period_start,
            period_end=period_end,
        )
        self._aggregates.append(aggregate)
        AggregateComputed(
            metric_name=metric_name,
            tenant_id=tenant_id,
            period=period.value,
            total_value=total_value,
        )
        self._log.info(
            "metering.aggregate.computed",
            metric=metric_name,
            tenant=tenant_id,
            total=total_value,
        )
        return aggregate

    async def get_usage_trends(
        self,
        metric_name: str,
        tenant_id: str,
        periods: int = 10,
    ) -> list[UsageAggregate]:
        relevant = [
            a for a in self._aggregates if a.metric_name == metric_name and a.tenant_id == tenant_id
        ]
        return relevant[-periods:]

    async def get_top_consumers(
        self,
        metric_name: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        tenant_totals: dict[str, float] = {}
        for rec in self._records.values():
            if rec.metric_name == metric_name:
                tenant_totals[rec.tenant_id] = (
                    tenant_totals.get(rec.tenant_id, 0.0) + rec.metric_value
                )
        sorted_tenants = sorted(tenant_totals.items(), key=lambda x: x[1], reverse=True)
        return [{"tenant_id": tid, "total_value": total} for tid, total in sorted_tenants[:limit]]

    async def generate_report(
        self,
        tenant_id: str,
        metric_names: list[str] | None = None,
        start: Any = None,
        end: Any = None,
    ) -> dict[str, Any]:
        report: dict[str, Any] = {
            "tenant_id": tenant_id,
            "period_start": str(start or "earliest"),
            "period_end": str(end or "latest"),
            "metrics": {},
        }
        metrics = metric_names or list(
            {r.metric_name for r in self._records.values() if r.tenant_id == tenant_id}
        )
        for m in metrics:
            try:
                agg = await self.aggregate(m, tenant_id, UsagePeriod.DAILY)
                report["metrics"][m] = agg.model_dump()
            except MetricNotFoundError:
                report["metrics"][m] = {"total_value": 0.0, "count": 0}
        self._log.info("metering.report.generated", tenant=tenant_id)
        return report


__all__ = ["MeteringService"]
