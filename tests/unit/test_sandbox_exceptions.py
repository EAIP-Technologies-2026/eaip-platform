"""Tests for sandbox exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.sandbox.exceptions import (
    EnvironmentNotFoundError,
    SandboxManagerError,
    SandboxNotFoundError,
)


class TestSandboxManagerError:
    def test_base_exception(self) -> None:
        err = SandboxManagerError("Manager error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestEnvironmentNotFoundError:
    def test_default_code(self) -> None:
        err = EnvironmentNotFoundError("Not found")
        assert isinstance(err, SandboxManagerError)
        assert err.code == ErrorCode.NOT_FOUND


class TestSandboxNotFoundError:
    def test_default_code(self) -> None:
        err = SandboxNotFoundError("Not found")
        assert isinstance(err, SandboxManagerError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = SandboxNotFoundError("Sandbox 'sb1' not found")
        assert "sb1" in str(err)
