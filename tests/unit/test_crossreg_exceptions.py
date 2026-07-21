"""Tests for :mod:`eaip.crossreg.exceptions`."""

from __future__ import annotations

from eaip.crossreg.exceptions import ReplicationError, RuleNotFoundError
from eaip.exceptions import ErrorCode


class TestReplicationError:
    def test_default_code(self) -> None:
        err = ReplicationError("Replication failed")
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestRuleNotFoundError:
    def test_default_code(self) -> None:
        err = RuleNotFoundError("Rule not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        assert issubclass(RuleNotFoundError, ReplicationError)
