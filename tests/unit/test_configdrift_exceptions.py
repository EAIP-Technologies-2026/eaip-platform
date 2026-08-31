"""Tests for configdrift exceptions."""

from __future__ import annotations

from eaip.configdrift.exceptions import (
    DriftDetectionError,
    SnapshotNotFoundError,
)
from eaip.exceptions.base import EAIPError, ErrorCode


class TestDriftDetectionError:
    def test_base_exception(self) -> None:
        err = DriftDetectionError("Drift error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestSnapshotNotFoundError:
    def test_default_code(self) -> None:
        err = SnapshotNotFoundError("Not found")
        assert isinstance(err, DriftDetectionError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = SnapshotNotFoundError("Snapshot 's1' not found")
        assert "s1" in str(err)
