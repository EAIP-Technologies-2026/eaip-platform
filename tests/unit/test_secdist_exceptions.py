"""Tests for :mod:`eaip.secdist.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.secdist.exceptions import (
    DistributionFailedError,
    DistributorError,
    TargetNotFoundError,
)


class TestDistributorError:
    def test_base_exception(self) -> None:
        err = DistributorError("distribution failed")
        assert str(err) == "distribution failed"
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_with_context(self) -> None:
        err = DistributorError("failed", context={"target": "t1"})
        assert err.context["target"] == "t1"


class TestTargetNotFoundError:
    def test_default_code(self) -> None:
        err = TargetNotFoundError("target not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_message(self) -> None:
        err = TargetNotFoundError("Target 'x' not found")
        assert "not found" in str(err)


class TestDistributionFailedError:
    def test_default_code(self) -> None:
        err = DistributionFailedError("distribution failed")
        assert err.code == ErrorCode.GATEWAY_ERROR

    def test_inheritance(self) -> None:
        err = DistributionFailedError("fail")
        assert isinstance(err, DistributorError)
