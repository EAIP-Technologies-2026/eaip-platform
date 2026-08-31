"""Tests for DataSyncService."""

from __future__ import annotations

import pytest

from eaip.datasync.exceptions import SyncJobNotFoundError
from eaip.datasync.models import SyncConfig, SyncJob, SyncRun, SyncStatus, SyncType
from eaip.datasync.sync import DataSyncService


class TestDataSyncService:
    @pytest.fixture
    def service(self) -> DataSyncService:
        return DataSyncService()

    @pytest.fixture
    def sample_job(self) -> SyncJob:
        return SyncJob(id="j1", name="sync-db", source="pg", target="bq", sync_type=SyncType.FULL)

    class TestCreateJob:
        async def test_creates_job(self, service: DataSyncService, sample_job: SyncJob) -> None:
            result = await service.create_job(sample_job)
            assert result.id == "j1"
            assert result.name == "sync-db"

        async def test_stores_job(self, service: DataSyncService, sample_job: SyncJob) -> None:
            await service.create_job(sample_job)
            stored = await service.get_job("j1")
            assert stored.id == "j1"

    class TestGetJob:
        async def test_returns_job(self, service: DataSyncService, sample_job: SyncJob) -> None:
            await service.create_job(sample_job)
            result = await service.get_job("j1")
            assert result.name == "sync-db"

        async def test_raises_on_missing(self, service: DataSyncService) -> None:
            with pytest.raises(SyncJobNotFoundError):
                await service.get_job("nonexistent")

    class TestUpdateJob:
        async def test_updates_job(self, service: DataSyncService, sample_job: SyncJob) -> None:
            await service.create_job(sample_job)
            updated = await service.update_job("j1", name="updated-sync")
            assert updated.name == "updated-sync"

        async def test_raises_on_missing(self, service: DataSyncService) -> None:
            with pytest.raises(SyncJobNotFoundError):
                await service.update_job("nonexistent", name="test")

    class TestDeleteJob:
        async def test_deletes_job(self, service: DataSyncService, sample_job: SyncJob) -> None:
            await service.create_job(sample_job)
            await service.delete_job("j1")
            assert await service.list_jobs() == []

        async def test_raises_on_missing(self, service: DataSyncService) -> None:
            with pytest.raises(SyncJobNotFoundError):
                await service.delete_job("nonexistent")

    class TestListJobs:
        async def test_empty_when_none(self, service: DataSyncService) -> None:
            assert await service.list_jobs() == []

        async def test_returns_all(self, service: DataSyncService, sample_job: SyncJob) -> None:
            await service.create_job(sample_job)
            jobs = await service.list_jobs()
            assert len(jobs) == 1

    class TestStartRun:
        async def test_starts_run(self, service: DataSyncService, sample_job: SyncJob) -> None:
            await service.create_job(sample_job)
            run = SyncRun(id="r1", job_id="j1")
            result = await service.start_run(run)
            assert result.status == SyncStatus.RUNNING

        async def test_raises_on_missing_job(self, service: DataSyncService) -> None:
            run = SyncRun(id="r1", job_id="nonexistent")
            with pytest.raises(SyncJobNotFoundError):
                await service.start_run(run)

    class TestCompleteRun:
        async def test_completes_run(self, service: DataSyncService, sample_job: SyncJob) -> None:
            await service.create_job(sample_job)
            run = SyncRun(id="r1", job_id="j1")
            await service.start_run(run)
            result = await service.complete_run("r1", items_synced=100)
            assert result.status == SyncStatus.COMPLETED
            assert result.items_synced == 100

    class TestFailRun:
        async def test_fails_run(self, service: DataSyncService, sample_job: SyncJob) -> None:
            await service.create_job(sample_job)
            run = SyncRun(id="r1", job_id="j1")
            await service.start_run(run)
            result = await service.fail_run("r1", error_message="error")
            assert result.status == SyncStatus.FAILED
            assert result.error_message == "error"

    class TestGetRun:
        async def test_returns_run(self, service: DataSyncService, sample_job: SyncJob) -> None:
            await service.create_job(sample_job)
            run = SyncRun(id="r1", job_id="j1")
            await service.start_run(run)
            result = await service.get_run("r1")
            assert result.id == "r1"

    class TestListRuns:
        async def test_lists_by_job(self, service: DataSyncService, sample_job: SyncJob) -> None:
            await service.create_job(sample_job)
            run = SyncRun(id="r1", job_id="j1")
            await service.start_run(run)
            runs = await service.list_runs(job_id="j1")
            assert len(runs) == 1

    class TestGetStatistics:
        async def test_returns_stats(self, service: DataSyncService, sample_job: SyncJob) -> None:
            await service.create_job(sample_job)
            stats = await service.get_statistics()
            assert stats["total_jobs"] == 1

    class TestConfig:
        def test_default_config(self) -> None:
            svc = DataSyncService()
            assert svc.config.max_concurrent_jobs == 5

        def test_custom_config(self) -> None:
            cfg = SyncConfig(max_concurrent_jobs=10)
            svc = DataSyncService(config=cfg)
            assert svc.config.max_concurrent_jobs == 10
