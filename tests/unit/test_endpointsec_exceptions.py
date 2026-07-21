"""Tests for :mod:`eaip.endpointsec.exceptions`."""

from __future__ import annotations

from eaip.endpointsec.exceptions import EndpointNotFoundError, EndpointScanError
from eaip.exceptions.base import ErrorCode


class TestEndpointScanError:
    def test_base_exception(self) -> None:
        err = EndpointScanError("scan error")
        assert str(err) == "scan error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestEndpointNotFoundError:
    def test_default_code(self) -> None:
        err = EndpointNotFoundError("not found")
        assert err.code == ErrorCode.ENDPOINT_NOT_FOUND

    def test_inheritance(self) -> None:
        err = EndpointNotFoundError("not found")
        assert isinstance(err, EndpointScanError)
