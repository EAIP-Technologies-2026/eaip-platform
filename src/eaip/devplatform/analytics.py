"""Usage analytics service — record, query, dashboard stats, and error rates."""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime
from typing import Any

from eaip.devplatform.events import UsageRecorded
from eaip.devplatform.models import UsageRecord


class UsageAnalyticsService:
    """Tracks and analyses API usage metrics."""

    def __init__(self) -> None:
        """Initialize UsageAnalyticsService with an empty store."""
        self._records: list[UsageRecord] = []
        self._event_handlers: list[Any] = []

    def on_event(self, handler: Any) -> None:
        """Register an event handler for usage analytics events.

        Args:
            handler: A callable that accepts event instances.
        """
        self._event_handlers.append(handler)

    def _emit(self, event: Any) -> None:
        """Emit an event to all registered handlers.

        Args:
            event: The event instance to emit.
        """
        for handler in self._event_handlers:
            handler(event)

    async def record_usage(self, record: UsageRecord) -> UsageRecord:
        """Record an API usage record.

        Args:
            record: The UsageRecord to record.

        Returns:
            The recorded UsageRecord.
        """
        self._records.append(record)
        self._emit(
            UsageRecorded(
                record_id=record.id,
                developer_id=record.developer_id,
                api_version=record.api_version,
                endpoint=record.endpoint,
                status_code=record.status_code,
                response_time_ms=record.response_time_ms,
            )
        )
        return record

    async def query_usage(
        self,
        developer_id: str | None = None,
        version: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> tuple[UsageRecord, ...]:
        """Query usage records with optional filters.

        Args:
            developer_id: Optional developer ID filter.
            version: Optional API version filter.
            start: Optional start datetime filter.
            end: Optional end datetime filter.

        Returns:
            A tuple of matching UsageRecord instances.
        """
        result = self._records[:]
        if developer_id is not None:
            result = [r for r in result if r.developer_id == developer_id]
        if version is not None:
            result = [r for r in result if r.api_version == version]
        if start is not None:
            result = [r for r in result if r.timestamp >= start]
        if end is not None:
            result = [r for r in result if r.timestamp <= end]
        return tuple(result)

    async def get_dashboard_stats(self) -> dict[str, Any]:
        """Get aggregate dashboard statistics.

        Returns:
            A dictionary with total_requests, unique_developers,
            total_errors, and average_response_time_ms.
        """
        total = len(self._records)
        developers = len({r.developer_id for r in self._records})
        errors = len([r for r in self._records if r.status_code >= 400])
        avg_response = (
            statistics.mean([r.response_time_ms for r in self._records]) if self._records else 0.0
        )
        total_bytes_sent = sum(r.bytes_sent for r in self._records)
        total_bytes_received = sum(r.bytes_received for r in self._records)
        return {
            "total_requests": total,
            "unique_developers": developers,
            "total_errors": errors,
            "average_response_time_ms": round(avg_response, 2),
            "total_bytes_sent": total_bytes_sent,
            "total_bytes_received": total_bytes_received,
        }

    async def get_popular_endpoints(self, limit: int = 10) -> tuple[tuple[str, int], ...]:
        """Get the most used endpoints ranked by request count.

        Args:
            limit: Maximum number of endpoints to return.

        Returns:
            A tuple of (endpoint, count) tuples sorted by count descending.
        """
        counts: dict[str, int] = defaultdict(int)
        for r in self._records:
            counts[r.endpoint] += 1
        sorted_endpoints = sorted(counts.items(), key=lambda x: -x[1])
        return tuple(sorted_endpoints[:limit])

    async def get_error_rates(self, version: str | None = None) -> dict[str, Any]:
        """Get error rates, optionally filtered by API version.

        Args:
            version: Optional API version filter.

        Returns:
            A dictionary with error_rate, total_requests, total_errors,
            and optionally a version breakdown.
        """
        records = self._records[:]
        if version is not None:
            records = [r for r in records if r.api_version == version]
        total = len(records)
        errors = len([r for r in records if r.status_code >= 400])
        error_rate = (errors / total * 100) if total > 0 else 0.0
        result: dict[str, Any] = {
            "error_rate": round(error_rate, 2),
            "total_requests": total,
            "total_errors": errors,
        }
        if version is not None:
            result["version"] = version
        return result

    async def get_response_time_percentiles(self) -> dict[str, float]:
        """Calculate response time percentiles (P50, P90, P95, P99).

        Returns:
            A dictionary with percentile keys mapped to response times in ms.
        """
        if not self._records:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}
        times = sorted(r.response_time_ms for r in self._records)
        n = len(times)
        return {
            "p50": round(times[int(n * 0.50)], 2),
            "p90": round(times[int(n * 0.90)], 2),
            "p95": round(times[int(n * 0.95)], 2),
            "p99": round(times[int(n * 0.99)], 2),
        }


__all__ = ["UsageAnalyticsService"]
