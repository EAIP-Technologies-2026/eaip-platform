"""Tests for :mod:`eaip.aivalidator.exceptions`."""

from __future__ import annotations

from eaip.aivalidator.exceptions import AIValidationError, RuleNotFoundError
from eaip.exceptions.base import ErrorCode


class TestAIValidationError:
    def test_base_exception(self) -> None:
        err = AIValidationError("validation error")
        assert str(err) == "validation error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestRuleNotFoundError:
    def test_default_code(self) -> None:
        err = RuleNotFoundError("not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = RuleNotFoundError("not found")
        assert isinstance(err, AIValidationError)
