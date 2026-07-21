"""Tests for :mod:`eaip.ratelimit.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.ratelimit.exceptions import RateLimitError, RateLimitExceededError


class TestRateLimitError:
    def test_base_exception(self) -> None:
        err = RateLimitError("rate limit error")
        assert str(err) == "rate limit error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestRateLimitExceededError:
    def test_default_code(self) -> None:
        err = RateLimitExceededError("rate limit exceeded")
        assert err.code == ErrorCode.RATE_LIMITED

    def test_inheritance(self) -> None:
        err = RateLimitExceededError("exceeded")
        assert isinstance(err, RateLimitError)
