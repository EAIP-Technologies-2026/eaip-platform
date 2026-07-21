"""Tests for retention exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.retention.exceptions import (
    PolicyNotFoundError,
    PurgeExecutionError,
    RetentionError,
)


class TestRetentionError:
    def test_base_exception(self) -> None:
        err = RetentionError("Retention error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestPolicyNotFoundError:
    def test_default_code(self) -> None:
        err = PolicyNotFoundError("Not found")
        assert isinstance(err, RetentionError)
        assert err.code == ErrorCode.NOT_FOUND


class TestPurgeExecutionError:
    def test_default_code(self) -> None:
        err = PurgeExecutionError("Purge failed")
        assert isinstance(err, RetentionError)
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_custom_message(self) -> None:
        err = PurgeExecutionError("Failed to purge policy 'p1'")
        assert "p1" in str(err)
