"""Tests for :mod:`eaip.eventret.exceptions`."""

from __future__ import annotations

from eaip.eventret.exceptions import EventRetentionError, PolicyNotFoundError
from eaip.exceptions.base import ErrorCode


class TestEventRetentionError:
    def test_base_exception(self) -> None:
        err = EventRetentionError("retention error")
        assert str(err) == "retention error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestPolicyNotFoundError:
    def test_default_code(self) -> None:
        err = PolicyNotFoundError("not found")
        assert err.code == ErrorCode.POLICY_NOT_FOUND

    def test_inheritance(self) -> None:
        err = PolicyNotFoundError("not found")
        assert isinstance(err, EventRetentionError)
