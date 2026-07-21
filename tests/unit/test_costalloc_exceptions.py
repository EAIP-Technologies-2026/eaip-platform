"""Tests for :mod:`eaip.costalloc.exceptions`."""

from __future__ import annotations

from eaip.costalloc.exceptions import CostAllocationError, RuleNotFoundError
from eaip.exceptions import ErrorCode


class TestCostAllocationError:
    def test_default_code(self) -> None:
        err = CostAllocationError("Something went wrong")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_with_context(self) -> None:
        err = CostAllocationError("Allocation failed", context={"allocation_id": "a1"})
        assert err.context["allocation_id"] == "a1"

    def test_with_code(self) -> None:
        err = CostAllocationError("Error", code=ErrorCode.VALIDATION_FAILED)
        assert err.code == ErrorCode.VALIDATION_FAILED


class TestRuleNotFoundError:
    def test_default_code(self) -> None:
        err = RuleNotFoundError("Rule r1 not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        assert issubclass(RuleNotFoundError, CostAllocationError)
