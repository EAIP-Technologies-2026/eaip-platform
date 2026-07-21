"""Tests for export exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.export.exceptions import (
    DeliveryFailedError,
    ExportError,
    ExportFailedError,
    FormatNotSupportedError,
    ReportNotFoundError,
    ScheduleNotFoundError,
)


class TestExportExceptionHierarchy:
    def test_export_error_is_eaip_error(self) -> None:
        assert issubclass(ExportError, EAIPError)

    def test_report_not_found_is_export_error(self) -> None:
        assert issubclass(ReportNotFoundError, ExportError)

    def test_export_failed_is_export_error(self) -> None:
        assert issubclass(ExportFailedError, ExportError)

    def test_format_not_supported_is_export_error(self) -> None:
        assert issubclass(FormatNotSupportedError, ExportError)

    def test_delivery_failed_is_export_error(self) -> None:
        assert issubclass(DeliveryFailedError, ExportError)

    def test_schedule_not_found_is_export_error(self) -> None:
        assert issubclass(ScheduleNotFoundError, ExportError)


class TestErrorCodes:
    def test_report_not_found_code(self) -> None:
        err = ReportNotFoundError("Not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_format_not_supported_code(self) -> None:
        err = FormatNotSupportedError("Bad format")
        assert err.code == ErrorCode.VALIDATION_FAILED

    def test_delivery_failed_code(self) -> None:
        err = DeliveryFailedError("Delivery failed")
        assert err.code == ErrorCode.GATEWAY_ERROR

    def test_schedule_not_found_code(self) -> None:
        err = ScheduleNotFoundError("Not found")
        assert err.code == ErrorCode.NOT_FOUND


class TestErrorMessage:
    def test_message_preserved(self) -> None:
        err = ReportNotFoundError("Custom message")
        assert str(err) == "Custom message"

    def test_context_supported(self) -> None:
        err = ExportFailedError("Failed", context={"job_id": "j1"})
        assert err.context["job_id"] == "j1"
