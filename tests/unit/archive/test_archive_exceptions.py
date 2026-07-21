"""Tests for Archive exceptions."""

from __future__ import annotations

from eaip.archive.exceptions import (
    ArchiveError,
    ArchiveNotFoundError,
    ArchiveStorageError,
    RetentionPolicyViolationError,
)
from eaip.exceptions.base import EAIPError, ErrorCode


class TestArchiveError:
    def test_is_eaiperror(self) -> None:
        err = ArchiveError("something went wrong")
        assert isinstance(err, EAIPError)
        assert err.code is ErrorCode.UNKNOWN

    def test_default_code(self) -> None:
        assert ArchiveError.default_code is ErrorCode.UNKNOWN


class TestArchiveNotFoundError:
    def test_message(self) -> None:
        err = ArchiveNotFoundError("rec_1")
        assert "rec_1" in str(err)
        assert err.record_id == "rec_1"
        assert err.code is ErrorCode.NOT_FOUND

    def test_default_code(self) -> None:
        assert ArchiveNotFoundError.default_code is ErrorCode.NOT_FOUND


class TestArchiveStorageError:
    def test_message(self) -> None:
        err = ArchiveStorageError("disk full")
        assert str(err) == "disk full"
        assert err.code is ErrorCode.INTERNAL_ERROR

    def test_default_code(self) -> None:
        assert ArchiveStorageError.default_code is ErrorCode.INTERNAL_ERROR


class TestRetentionPolicyViolationError:
    def test_message(self) -> None:
        err = RetentionPolicyViolationError("p_1", "size limit exceeded")
        assert err.policy_id == "p_1"
        assert "size limit exceeded" in str(err)
        assert err.code is ErrorCode.POLICY_VIOLATION

    def test_default_code(self) -> None:
        assert RetentionPolicyViolationError.default_code is ErrorCode.POLICY_VIOLATION
