"""Tests for long-running job executor."""

from __future__ import annotations

import asyncio

import pytest

from eaip.jobs.executor import LongRunningJob, LongRunningJobExecutor
from eaip.jobs.models import JobRun, JobStatus, RetryConfig


class _SimpleHandler:
    async def execute(self, run: JobRun) -> str:
        return f"processed: {run.job_id}"

    async def cancel(self, run_id: str) -> None:
        pass

    async def checkpoint(self, run_id: str, data: dict) -> None:
        pass


class TestLongRunningJob:
    @pytest.mark.asyncio
    async def test_execute_success(self) -> None:
        handler = _SimpleHandler()
        job = LongRunningJob(job_id="job_1", handler=handler)
        run = JobRun(id="run_1", job_id="job_1", job_name="Test")
        result = await job.execute(run)
        assert result.status is JobStatus.COMPLETED
        assert "processed" in result.result

    @pytest.mark.asyncio
    async def test_execute_with_retry(self) -> None:
        call_count = 0

        class _FailingHandler:
            async def execute(self, run: JobRun) -> str:
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise RuntimeError("transient error")
                return "success on retry"

            async def cancel(self, run_id: str) -> None:
                pass

            async def checkpoint(self, run_id: str, data: dict) -> None:
                pass

        handler = _FailingHandler()
        job = LongRunningJob(
            job_id="job_2", handler=handler,
            retry_config=RetryConfig(max_retries=2, delay_seconds=0.01),
        )
        run = JobRun(id="run_2", job_id="job_2")
        result = await job.execute(run)
        assert result.status is JobStatus.COMPLETED
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_execute_timeout(self) -> None:
        class _SlowHandler:
            async def execute(self, run: JobRun) -> str:
                await asyncio.sleep(10)
                return "too late"

            async def cancel(self, run_id: str) -> None:
                pass

            async def checkpoint(self, run_id: str, data: dict) -> None:
                pass

        handler = _SlowHandler()
        job = LongRunningJob(job_id="job_3", handler=handler, timeout_seconds=0.01)
        run = JobRun(id="run_3", job_id="job_3")
        result = await job.execute(run)
        assert result.status is JobStatus.FAILED
        assert "timed out" in (result.error or "")

    @pytest.mark.asyncio
    async def test_cancel(self) -> None:
        handler = _SimpleHandler()
        job = LongRunningJob(job_id="job_4", handler=handler)
        run = JobRun(id="run_4", job_id="job_4")
        task = asyncio.create_task(job.execute(run))
        await asyncio.sleep(0.01)
        await job.cancel("run_4")
        result = await task
        assert result.status in (JobStatus.CANCELLED, JobStatus.COMPLETED)

    @pytest.mark.asyncio
    async def test_report_progress(self) -> None:
        handler = _SimpleHandler()
        job = LongRunningJob(job_id="job_5", handler=handler)
        run = JobRun(id="run_5", job_id="job_5")
        await job.execute(run)
        await job.report_progress("run_5", 0.5, "halfway")
        saved = job.get_run("run_5")
        assert saved is not None
        assert saved.progress == 0.5

    @pytest.mark.asyncio
    async def test_save_checkpoint(self) -> None:
        handler = _SimpleHandler()
        job = LongRunningJob(job_id="job_6", handler=handler)
        run = JobRun(id="run_6", job_id="job_6")
        await job.execute(run)
        await job.save_checkpoint("run_6", {"offset": 100})
        saved = job.get_run("run_6")
        assert saved is not None
        assert saved.checkpoint_data == {"offset": 100}

    def test_list_runs(self) -> None:
        handler = _SimpleHandler()
        job = LongRunningJob(job_id="job_7", handler=handler)
        assert job.list_runs() == []

    def test_get_run_not_found(self) -> None:
        handler = _SimpleHandler()
        job = LongRunningJob(job_id="job_8", handler=handler)
        assert job.get_run("nonexistent") is None


class TestLongRunningJobExecutor:
    @pytest.mark.asyncio
    async def test_register_and_execute(self) -> None:
        executor = LongRunningJobExecutor()
        handler = _SimpleHandler()
        job = LongRunningJob(job_id="job_e1", handler=handler)
        executor.register_job(job)
        run = JobRun(id="run_e1", job_id="job_e1")
        result = await executor.execute_job("job_e1", run)
        assert result.status is JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_nonexistent_job(self) -> None:
        executor = LongRunningJobExecutor()
        with pytest.raises(Exception):
            await executor.execute_job("nonexistent", JobRun(id="r", job_id="x"))
