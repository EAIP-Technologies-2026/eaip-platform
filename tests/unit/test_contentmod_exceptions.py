"""Tests for :mod:`eaip.contentmod.exceptions`."""

from __future__ import annotations

from eaip.contentmod.exceptions import ModerationError, RuleNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestModerationError:
    def test_base_exception(self) -> None:
        err = ModerationError("moderation failed")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert str(err) == "moderation failed"


class TestRuleNotFoundError:
    def test_default_code(self) -> None:
        err = RuleNotFoundError("rule not found")
        assert isinstance(err, ModerationError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = RuleNotFoundError("Rule 'r1' not found")
        assert "r1" in str(err)
