"""Tests for API Documentation exceptions."""

from __future__ import annotations

from eaip.apidocs.exceptions import (
    ApiDocsError,
    ChangelogError,
    DocGenerationError,
    DocNotFoundError,
)
from eaip.exceptions.base import EAIPError, ErrorCode


class TestApiDocsError:
    def test_is_eaip_error(self) -> None:
        assert issubclass(ApiDocsError, EAIPError)


class TestDocGenerationError:
    def test_message(self) -> None:
        err = DocGenerationError("failed to generate spec")
        assert "failed to generate spec" in str(err)


class TestDocNotFoundError:
    def test_message(self) -> None:
        err = DocNotFoundError("doc_42")
        assert "doc_42" in str(err)
        assert err.doc_id == "doc_42"

    def test_error_code(self) -> None:
        err = DocNotFoundError("d1")
        assert err.code is ErrorCode.NOT_FOUND


class TestChangelogError:
    def test_message(self) -> None:
        err = ChangelogError("version is required")
        assert "version is required" in str(err)

    def test_hierarchy(self) -> None:
        assert issubclass(DocGenerationError, ApiDocsError)
        assert issubclass(DocNotFoundError, ApiDocsError)
        assert issubclass(ChangelogError, ApiDocsError)
