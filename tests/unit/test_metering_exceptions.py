"""Tests for metering exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.metering.exceptions import MeteringError, MetricNotFoundError


class TestMeteringError:
    def test_base_exception(self) -> None:
        err = MeteringError("Metering error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestMetricNotFoundError:
    def test_default_code(self) -> None:
        err = MetricNotFoundError("Not found")
        assert isinstance(err, MeteringError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = MetricNotFoundError("Metric 'api_calls' not found")
        assert "api_calls" in str(err)
