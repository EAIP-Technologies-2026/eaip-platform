"""Tests for :mod:`eaip.firewall.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.firewall.exceptions import FirewallError, RuleNotFoundError


class TestFirewallError:
    def test_base_exception(self) -> None:
        err = FirewallError("firewall error")
        assert str(err) == "firewall error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestRuleNotFoundError:
    def test_default_code(self) -> None:
        err = RuleNotFoundError("rule not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = RuleNotFoundError("not found")
        assert isinstance(err, FirewallError)
