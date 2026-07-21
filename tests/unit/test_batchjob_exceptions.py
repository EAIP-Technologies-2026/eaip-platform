"""Tests for batchjob exceptions."""

from __future__ import annotations

from eaip.batchjob.exceptions import BatchJobError, BatchJobNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestBatchJobError:
    def test_base_exception(self) -> None:
        err = BatchJobError("Batch job error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert str(err) == "Batch job error"

    def test_with_context(self) -> None:
        err = BatchJobError("Error", context={"job_id": "j1"})
        assert err.context == {"job_id": "j1"}


class TestBatchJobNotFoundError:
    def test_default_code(self) -> None:
        err = BatchJobNotFoundError("Job not found")
        assert isinstance(err, BatchJobError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = BatchJobNotFoundError("Job 'xyz' not found")
        assert "xyz" in str(err)
