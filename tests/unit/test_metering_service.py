"""Tests for MeteringService."""

from __future__ import annotations

import pytest

from eaip.metering.exceptions import MetricNotFoundError
from eaip.metering.models import MeteringConfig, MeteringRecord
from eaip.metering.service import MeteringService


class TestMeteringService:
    @pytest.fixture
    def service(self) -> MeteringService:
        return MeteringService()

    @pytest.fixture
    def sample_record(self) -> MeteringRecord:
        return MeteringRecord(
            id="r1", tenant_id="tenant1", metric_name="api_calls", metric_value=100.0
        )

    class TestRecordUsage:
        async def test_record(
            self, service: MeteringService, sample_record: MeteringRecord
        ) -> None:
            result = await service.record_usage(sample_record)
            assert result.id == "r1"
            assert result.metric_value == 100.0

        async def test_record_multiple(
            self, service: MeteringService, sample_record: MeteringRecord
        ) -> None:
            await service.record_usage(sample_record)
            r2 = MeteringRecord(
                id="r2", tenant_id="tenant1", metric_name="api_calls", metric_value=50.0
            )
            await service.record_usage(r2)
            records = await service.query_usage("tenant1", "api_calls")
            assert len(records) == 2

    class TestQueryUsage:
        async def test_query(self, service: MeteringService, sample_record: MeteringRecord) -> None:
            await service.record_usage(sample_record)
            records = await service.query_usage("tenant1", "api_calls")
            assert len(records) == 1

        async def test_query_no_results(self, service: MeteringService) -> None:
            records = await service.query_usage("tenant1", "nonexistent")
            assert len(records) == 0

    class TestAggregate:
        async def test_aggregate(
            self, service: MeteringService, sample_record: MeteringRecord
        ) -> None:
            await service.record_usage(sample_record)
            agg = await service.aggregate("api_calls", "tenant1")
            assert agg.total_value == 100.0
            assert agg.count == 1
            assert agg.average_value == 100.0

        async def test_aggregate_no_data(self, service: MeteringService) -> None:
            with pytest.raises(MetricNotFoundError):
                await service.aggregate("api_calls", "tenant1")

    class TestGetUsageTrends:
        async def test_trends(
            self, service: MeteringService, sample_record: MeteringRecord
        ) -> None:
            await service.record_usage(sample_record)
            await service.aggregate("api_calls", "tenant1")
            trends = await service.get_usage_trends("api_calls", "tenant1")
            assert len(trends) == 1

    class TestGetTopConsumers:
        async def test_top_consumers(
            self, service: MeteringService, sample_record: MeteringRecord
        ) -> None:
            await service.record_usage(sample_record)
            r2 = MeteringRecord(
                id="r2", tenant_id="tenant2", metric_name="api_calls", metric_value=200.0
            )
            await service.record_usage(r2)
            top = await service.get_top_consumers("api_calls", limit=5)
            assert len(top) == 2
            assert top[0]["tenant_id"] == "tenant2"

    class TestGenerateReport:
        async def test_report(
            self, service: MeteringService, sample_record: MeteringRecord
        ) -> None:
            await service.record_usage(sample_record)
            report = await service.generate_report("tenant1")
            assert report["tenant_id"] == "tenant1"
            assert "api_calls" in report["metrics"]

    class TestConfig:
        def test_default_config(self) -> None:
            s = MeteringService()
            assert s.config.retention_days == 90
            assert s.config.aggregation_interval_minutes == 60

        def test_custom_config(self) -> None:
            config = MeteringConfig(retention_days=30, aggregation_interval_minutes=15)
            s = MeteringService(config=config)
            assert s.config.retention_days == 30
            assert s.config.aggregation_interval_minutes == 15
