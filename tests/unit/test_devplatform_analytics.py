"""Tests for :mod:`eaip.devplatform.analytics`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from eaip.devplatform.analytics import UsageAnalyticsService
from eaip.devplatform.events import UsageRecorded
from eaip.devplatform.models import UsageRecord


@pytest.fixture
def service() -> UsageAnalyticsService:
    return UsageAnalyticsService()


@pytest.fixture
def sample_records(service: UsageAnalyticsService) -> UsageAnalyticsService:
    """Populate the service with sample usage records."""
    records = [
        UsageRecord(
            id="r1",
            developer_id="d1",
            api_version="1.0.0",
            endpoint="/users",
            response_time_ms=100,
            status_code=200,
        ),
        UsageRecord(
            id="r2",
            developer_id="d1",
            api_version="1.0.0",
            endpoint="/users",
            response_time_ms=200,
            status_code=200,
        ),
        UsageRecord(
            id="r3",
            developer_id="d2",
            api_version="2.0.0",
            endpoint="/items",
            response_time_ms=300,
            status_code=500,
        ),
        UsageRecord(
            id="r4",
            developer_id="d1",
            api_version="2.0.0",
            endpoint="/items",
            response_time_ms=50,
            status_code=200,
        ),
        UsageRecord(
            id="r5",
            developer_id="d2",
            api_version="1.0.0",
            endpoint="/users",
            response_time_ms=400,
            status_code=404,
        ),
    ]
    for rec in records:
        # Use direct append to avoid event emission for test setup
        service._records.append(rec)
    return service


class TestUsageAnalyticsService:
    async def test_record_usage(self, service: UsageAnalyticsService) -> None:
        record = UsageRecord(id="r1", developer_id="d1", api_version="1.0.0", endpoint="/users")
        result = await service.record_usage(record)
        assert result.id == "r1"

    async def test_record_usage_emits_event(self, service: UsageAnalyticsService) -> None:
        events: list[UsageRecorded] = []
        service.on_event(events.append)
        record = UsageRecord(id="r1", developer_id="d1", api_version="1.0.0", endpoint="/users")
        await service.record_usage(record)
        assert len(events) == 1
        assert events[0].record_id == "r1"

    async def test_query_usage_all(self, sample_records: UsageAnalyticsService) -> None:
        records = await sample_records.query_usage()
        assert len(records) == 5

    async def test_query_usage_by_developer(self, sample_records: UsageAnalyticsService) -> None:
        records = await sample_records.query_usage(developer_id="d1")
        assert len(records) == 3

    async def test_query_usage_by_version(self, sample_records: UsageAnalyticsService) -> None:
        records = await sample_records.query_usage(version="2.0.0")
        assert len(records) == 2

    async def test_query_usage_by_time_range(self, sample_records: UsageAnalyticsService) -> None:
        now = datetime.now(UTC)
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        records = await sample_records.query_usage(start=start, end=end)
        assert len(records) == 5

    async def test_get_dashboard_stats(self, sample_records: UsageAnalyticsService) -> None:
        stats = await sample_records.get_dashboard_stats()
        assert stats["total_requests"] == 5
        assert stats["unique_developers"] == 2
        assert stats["total_errors"] == 2

    async def test_get_dashboard_stats_empty(self, service: UsageAnalyticsService) -> None:
        stats = await service.get_dashboard_stats()
        assert stats["total_requests"] == 0
        assert stats["average_response_time_ms"] == 0.0

    async def test_get_popular_endpoints(self, sample_records: UsageAnalyticsService) -> None:
        popular = await sample_records.get_popular_endpoints(limit=2)
        assert len(popular) == 2
        assert popular[0][0] == "/users"
        assert popular[0][1] == 3

    async def test_get_error_rates(self, sample_records: UsageAnalyticsService) -> None:
        rates = await sample_records.get_error_rates()
        assert rates["total_requests"] == 5
        assert rates["total_errors"] == 2
        assert rates["error_rate"] == 40.0

    async def test_get_error_rates_by_version(self, sample_records: UsageAnalyticsService) -> None:
        rates = await sample_records.get_error_rates(version="1.0.0")
        assert rates["total_requests"] == 3
        assert rates["version"] == "1.0.0"

    async def test_get_response_time_percentiles(
        self, sample_records: UsageAnalyticsService
    ) -> None:
        p = await sample_records.get_response_time_percentiles()
        assert p["p50"] > 0
        assert p["p95"] >= p["p50"]

    async def test_get_response_time_percentiles_empty(
        self, service: UsageAnalyticsService
    ) -> None:
        p = await service.get_response_time_percentiles()
        assert p["p50"] == 0.0
        assert p["p99"] == 0.0

    async def test_multiple_records_same_endpoint(self, service: UsageAnalyticsService) -> None:
        for i in range(5):
            await service.record_usage(
                UsageRecord(id=f"r{i}", developer_id="d1", api_version="1.0.0", endpoint="/test")
            )
        popular = await service.get_popular_endpoints()
        assert popular[0] == ("/test", 5)
