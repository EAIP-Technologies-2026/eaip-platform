"""Tests for etemplate exceptions."""

from __future__ import annotations

from eaip.etemplate.exceptions import (
    TemplateEngineError,
    TemplateNotFoundError,
    TemplateRenderError,
)
from eaip.exceptions.base import EAIPError, ErrorCode


class TestTemplateEngineError:
    def test_base_exception(self) -> None:
        err = TemplateEngineError("Engine error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestTemplateNotFoundError:
    def test_default_code(self) -> None:
        err = TemplateNotFoundError("Not found")
        assert isinstance(err, TemplateEngineError)
        assert err.code == ErrorCode.NOT_FOUND


class TestTemplateRenderError:
    def test_default_code(self) -> None:
        err = TemplateRenderError("Render failed")
        assert isinstance(err, TemplateEngineError)
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_custom_message(self) -> None:
        err = TemplateRenderError("Variable 'x' missing")
        assert "x" in str(err)
