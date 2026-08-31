"""Tests for BatchJobScheduler service."""

from __future__ import annotations

import pytest

from eaip.batchjob.exceptions import BatchJobError, BatchJobNotFoundError
from eaip.batchjob.models import BatchJob, BatchJobConfig, BatchJobStatus
from eaip.batchjob.scheduler import BatchJobScheduler


class TestBatchJobScheduler:
    @pytest.fixture
    def scheduler(self) -> BatchJobScheduler:
        return BatchJobScheduler()

    @pytest.fixture
    def sample_job(self) -> BatchJob:
        return BatchJob(
            id="job1",
            name="Data export",
            job_type="export",
            priority=5,
            parameters={"format": "csv"},
            schedule_cron="0 0 * * *",
        )

    class TestCreateJob:
        async def test_create_job(self, scheduler: BatchJobScheduler, sample_job: BatchJob) -> None:
            result = await scheduler.create_job(sample_job)
            assert result.id == "job1"
            assert result.name == "Data export"

        async def test_list_jobs(self, scheduler: BatchJobScheduler, sample_job: BatchJob) -> None:
            await scheduler.create_job(sample_job)
            jobs = await scheduler.list_jobs()
            assert len(jobs) == 1

    class TestGetJob:
        async def test_get_job(self, scheduler: BatchJobScheduler, sample_job: BatchJob) -> None:
            await scheduler.create_job(sample_job)
            job = await scheduler.get_job("job1")
            assert job.job_type == "export"

        async def test_get_job_not_found(self, scheduler: BatchJobScheduler) -> None:
            with pytest.raises(BatchJobNotFoundError):
                await scheduler.get_job("nonexistent")

    class TestStartExecution:
        async def test_start_execution(
            self, scheduler: BatchJobScheduler, sample_job: BatchJob
        ) -> None:
            await scheduler.create_job(sample_job)
            execution = await scheduler.start_execution("job1")
            assert execution.status == BatchJobStatus.RUNNING
            assert execution.job_id == "job1"

        async def test_start_execution_disabled_job(self, scheduler: BatchJobScheduler) -> None:
            job = BatchJob(id="job1", name="Disabled", job_type="test", enabled=False)
            await scheduler.create_job(job)
            with pytest.raises(BatchJobError):
                await scheduler.start_execution("job1")

        async def test_start_execution_job_not_found(self, scheduler: BatchJobScheduler) -> None:
            with pytest.raises(BatchJobNotFoundError):
                await scheduler.start_execution("nonexistent")

    class TestCompleteExecution:
        async def test_complete_execution(
            self, scheduler: BatchJobScheduler, sample_job: BatchJob
        ) -> None:
            await scheduler.create_job(sample_job)
            execution = await scheduler.start_execution("job1")
            result = {"rows": 100}
            completed = await scheduler.complete_execution(execution.id, result)
            assert completed.status == BatchJobStatus.COMPLETED
            assert completed.result == {"rows": 100}

        async def test_complete_execution_not_found(self, scheduler: BatchJobScheduler) -> None:
            with pytest.raises(BatchJobNotFoundError):
                await scheduler.complete_execution("nonexistent")

    class TestFailExecution:
        async def test_fail_execution(
            self, scheduler: BatchJobScheduler, sample_job: BatchJob
        ) -> None:
            await scheduler.create_job(sample_job)
            execution = await scheduler.start_execution("job1")
            failed = await scheduler.fail_execution(execution.id, "Timeout", retry_count=1)
            assert failed.status == BatchJobStatus.FAILED
            assert failed.error == "Timeout"

        async def test_fail_execution_not_found(self, scheduler: BatchJobScheduler) -> None:
            with pytest.raises(BatchJobNotFoundError):
                await scheduler.fail_execution("nonexistent", "Error")

    class TestGetExecution:
        async def test_get_execution(
            self, scheduler: BatchJobScheduler, sample_job: BatchJob
        ) -> None:
            await scheduler.create_job(sample_job)
            execution = await scheduler.start_execution("job1")
            result = await scheduler.get_execution(execution.id)
            assert result.job_id == "job1"

        async def test_get_execution_not_found(self, scheduler: BatchJobScheduler) -> None:
            with pytest.raises(BatchJobNotFoundError):
                await scheduler.get_execution("nonexistent")

    class TestListExecutions:
        async def test_list_all(self, scheduler: BatchJobScheduler, sample_job: BatchJob) -> None:
            await scheduler.create_job(sample_job)
            e1 = await scheduler.start_execution("job1")
            e2 = await scheduler.start_execution("job1")
            executions = await scheduler.list_executions()
            assert len(executions) == 2

        async def test_list_by_job(self, scheduler: BatchJobScheduler) -> None:
            j1 = BatchJob(id="j1", name="Job 1", job_type="test")
            j2 = BatchJob(id="j2", name="Job 2", job_type="test")
            await scheduler.create_job(j1)
            await scheduler.create_job(j2)
            await scheduler.start_execution("j1")
            await scheduler.start_execution("j1")
            await scheduler.start_execution("j2")
            executions = await scheduler.list_executions("j1")
            assert len(executions) == 2

    class TestConfig:
        def test_default_config(self) -> None:
            s = BatchJobScheduler()
            assert s.config.max_concurrent_jobs == 10
            assert s.config.default_timeout_seconds == 3600

        def test_custom_config(self) -> None:
            config = BatchJobConfig(max_concurrent_jobs=5, poll_interval_seconds=15)
            s = BatchJobScheduler(config=config)
            assert s.config.max_concurrent_jobs == 5
            assert s.config.poll_interval_seconds == 15
