"""Tests for :mod:`eaip.backupver.exceptions`."""

from __future__ import annotations

from eaip.backupver.exceptions import BackupNotFoundError, BackupVerificationError
from eaip.exceptions.base import ErrorCode


class TestBackupVerificationError:
    def test_base_exception(self) -> None:
        err = BackupVerificationError("verification error")
        assert str(err) == "verification error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestBackupNotFoundError:
    def test_default_code(self) -> None:
        err = BackupNotFoundError("backup not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = BackupNotFoundError("not found")
        assert isinstance(err, BackupVerificationError)
