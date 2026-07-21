"""Tests for config backup exception hierarchy."""

from __future__ import annotations

from eaip.configbackup.exceptions import ConfigBackupError, SnapshotNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestConfigBackupError:
    def test_is_eaip_error(self) -> None:
        err = ConfigBackupError("generic error")
        assert isinstance(err, EAIPError)

    def test_default_code(self) -> None:
        err = ConfigBackupError("test")
        assert err.code == ErrorCode.UNKNOWN


class TestSnapshotNotFoundError:
    def test_inherits_config_backup_error(self) -> None:
        err = SnapshotNotFoundError("not found")
        assert isinstance(err, ConfigBackupError)

    def test_default_code(self) -> None:
        err = SnapshotNotFoundError("missing")
        assert err.code == ErrorCode.NOT_FOUND
