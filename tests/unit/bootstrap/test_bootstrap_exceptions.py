"""Tests for Bootstrap exceptions."""

from __future__ import annotations

from eaip.bootstrap.exceptions import (
    BootstrapError,
    FileGenerationError,
    ScaffoldError,
    TemplateNotFoundError,
)
from eaip.exceptions.base import EAIPError, ErrorCode


class TestBootstrapError:
    def test_is_eaip_error(self) -> None:
        assert issubclass(BootstrapError, EAIPError)


class TestTemplateNotFoundError:
    def test_message(self) -> None:
        err = TemplateNotFoundError("tpl_42")
        assert "tpl_42" in str(err)

    def test_error_code(self) -> None:
        err = TemplateNotFoundError("t1")
        assert err.code is ErrorCode.NOT_FOUND


class TestScaffoldError:
    def test_message(self) -> None:
        err = ScaffoldError("tpl_1", "template is inactive")
        assert "tpl_1" in str(err)
        assert "inactive" in str(err)


class TestFileGenerationError:
    def test_message(self) -> None:
        err = FileGenerationError("src/main.py", "permission denied")
        assert "src/main.py" in str(err)
        assert err.file_path == "src/main.py"

    def test_hierarchy(self) -> None:
        assert issubclass(TemplateNotFoundError, BootstrapError)
        assert issubclass(ScaffoldError, BootstrapError)
        assert issubclass(FileGenerationError, BootstrapError)
