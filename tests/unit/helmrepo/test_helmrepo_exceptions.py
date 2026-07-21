"""Tests for :mod:`eaip.helmrepo.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.helmrepo.exceptions import ChartNotFoundError, HelmError


class TestHelmExceptionHierarchy:
    def test_helm_error_is_eaip_error(self) -> None:
        assert issubclass(HelmError, EAIPError)

    def test_not_found_is_helm_error(self) -> None:
        assert issubclass(ChartNotFoundError, HelmError)


class TestErrorCodes:
    def test_helm_error_code(self) -> None:
        err = HelmError("test")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_not_found_code(self) -> None:
        err = ChartNotFoundError("not found")
        assert err.code == ErrorCode.NOT_FOUND


class TestErrorMessage:
    def test_message_preserved(self) -> None:
        err = ChartNotFoundError("Custom message")
        assert str(err) == "Custom message"

    def test_context_supported(self) -> None:
        err = HelmError("bad", context={"chart_id": "c1"})
        assert err.context["chart_id"] == "c1"
