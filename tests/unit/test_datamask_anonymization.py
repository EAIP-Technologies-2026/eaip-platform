"""Tests for :mod:`eaip.datamask.anonymization`."""

from __future__ import annotations

import pytest

from eaip.datamask.anonymization import AnonymizationService
from eaip.datamask.models import DataType, JobStatus, MaskingRule, MaskingStrategy


class TestAnonymizationService:
    @pytest.fixture
    def service(self) -> AnonymizationService:
        return AnonymizationService()

    async def test_create_job(self, service: AnonymizationService) -> None:
        rule = MaskingRule(
            id="r1",
            name="Email Mask",
            field_pattern="email",
            data_type=DataType.EMAIL,
            strategy=MaskingStrategy.MASK,
        )
        job = await service.create_job(source="db://users", rules=(rule,), name="test-job")
        assert job.name == "test-job"
        assert job.source == "db://users"
        assert len(job.rules) == 1
        assert job.status is JobStatus.PENDING

    async def test_create_job_default_name(self, service: AnonymizationService) -> None:
        job = await service.create_job(source="s3://data", rules=())
        assert job.name.startswith("anonymization-")

    async def test_get_job(self, service: AnonymizationService) -> None:
        job = await service.create_job(source="src", rules=())
        fetched = await service.get_job(job.id)
        assert fetched.id == job.id
        assert fetched.name == job.name

    async def test_get_job_not_found(self, service: AnonymizationService) -> None:
        with pytest.raises(Exception):
            await service.get_job("nonexistent")

    async def test_execute_job(self, service: AnonymizationService) -> None:
        job = await service.create_job(source="db://test", rules=())
        result = await service.execute_job(job.id)
        assert result.status is JobStatus.COMPLETED

    async def test_execute_job_nonexistent(self, service: AnonymizationService) -> None:
        with pytest.raises(Exception):
            await service.execute_job("nonexistent")

    async def test_execute_job_with_rules(self, service: AnonymizationService) -> None:
        rule = MaskingRule(
            id="r1",
            name="Email",
            field_pattern="email",
            data_type=DataType.EMAIL,
            strategy=MaskingStrategy.MASK,
        )
        job = await service.create_job(source="db://test", rules=(rule,))
        result = await service.execute_job(job.id)
        assert result.status is JobStatus.COMPLETED

    async def test_list_jobs(self, service: AnonymizationService) -> None:
        await service.create_job(source="s1", rules=())
        await service.create_job(source="s2", rules=())
        jobs = await service.list_jobs()
        assert len(jobs) == 2

    async def test_list_jobs_filter_by_status(self, service: AnonymizationService) -> None:
        j1 = await service.create_job(source="s1", rules=())
        await service.execute_job(j1.id)
        pending = await service.list_jobs(status=JobStatus.PENDING)
        completed = await service.list_jobs(status=JobStatus.COMPLETED)
        assert len(completed) == 1
        assert len(pending) == 0

    async def test_list_jobs_limit(self, service: AnonymizationService) -> None:
        for i in range(5):
            await service.create_job(source=f"s{i}", rules=())
        jobs = await service.list_jobs(limit=3)
        assert len(jobs) == 3
