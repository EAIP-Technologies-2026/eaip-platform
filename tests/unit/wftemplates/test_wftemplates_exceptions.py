"""Tests for Workflow Template exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.wftemplates.exceptions import (
    CategoryNotFoundError,
    TemplateError,
    TemplateImportError,
    TemplateNotFoundError,
)


class TestTemplateError:
    def test_is_eaip_error(self) -> None:
        assert issubclass(TemplateError, EAIPError)

    def test_default_code(self) -> None:
        err = TemplateError("test")
        assert err.code is ErrorCode.INTERNAL_ERROR


class TestTemplateNotFoundError:
    def test_message(self) -> None:
        err = TemplateNotFoundError("tpl_42")
        assert "tpl_42" in str(err)
        assert err.template_id == "tpl_42"

    def test_error_code(self) -> None:
        err = TemplateNotFoundError("t1")
        assert err.code is ErrorCode.NOT_FOUND


class TestCategoryNotFoundError:
    def test_message(self) -> None:
        err = CategoryNotFoundError("cat_42")
        assert "cat_42" in str(err)

    def test_error_code(self) -> None:
        err = CategoryNotFoundError("c1")
        assert err.code is ErrorCode.NOT_FOUND


class TestTemplateImportError:
    def test_message(self) -> None:
        err = TemplateImportError("tpl_1", "invalid status")
        assert "tpl_1" in str(err)
        assert "invalid status" in str(err)

    def test_hierarchy(self) -> None:
        assert issubclass(TemplateNotFoundError, TemplateError)
        assert issubclass(CategoryNotFoundError, TemplateError)
        assert issubclass(TemplateImportError, TemplateError)
