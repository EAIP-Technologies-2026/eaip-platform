"""Tests for auditview exceptions."""

from __future__ import annotations

from eaip.auditview.exceptions import AuditViewerError, EntryNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestAuditViewerError:
    def test_base_exception(self) -> None:
        err = AuditViewerError("Viewer error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestEntryNotFoundError:
    def test_default_code(self) -> None:
        err = EntryNotFoundError("Not found")
        assert isinstance(err, AuditViewerError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = EntryNotFoundError("Entry 'e1' not found")
        assert "e1" in str(err)
