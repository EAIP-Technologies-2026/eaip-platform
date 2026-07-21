"""Tests for alertcorr exceptions."""

from __future__ import annotations

from eaip.alertcorr.exceptions import CorrelationError, RuleNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestCorrelationError:
    def test_base_exception(self) -> None:
        err = CorrelationError("Correlation error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert str(err) == "Correlation error"

    def test_with_context(self) -> None:
        err = CorrelationError("Error", context={"rule_id": "r1"})
        assert err.context == {"rule_id": "r1"}


class TestRuleNotFoundError:
    def test_default_code(self) -> None:
        err = RuleNotFoundError("Rule not found")
        assert isinstance(err, CorrelationError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = RuleNotFoundError("Rule 'xyz' not found")
        assert "xyz" in str(err)
