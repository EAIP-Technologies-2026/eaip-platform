"""Tests for :mod:`eaip.datasync.exceptions`."""

from __future__ import annotations

from eaip.datasync.exceptions import SyncError, SyncJobNotFoundError
from eaip.exceptions.base import ErrorCode


class TestSyncError:
    def test_base_exception(self) -> None:
        err = SyncError("sync error")
        assert str(err) == "sync error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestSyncJobNotFoundError:
    def test_default_code(self) -> None:
        err = SyncJobNotFoundError("job not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = SyncJobNotFoundError("not found")
        assert isinstance(err, SyncError)
