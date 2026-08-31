"""Tests for Script Runtime exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.script.exceptions import (
    FunctionNotFoundError,
    SandboxViolationError,
    ScriptError,
    ScriptExecutionError,
    ScriptTimeoutError,
)


class TestScriptError:
    def test_is_eaip_error(self) -> None:
        assert issubclass(ScriptError, EAIPError)

    def test_default_error_code(self) -> None:
        err = ScriptError("something went wrong")
        assert err.code is ErrorCode.INTERNAL_ERROR


class TestFunctionNotFoundError:
    def test_message_includes_id(self) -> None:
        err = FunctionNotFoundError("fn_42")
        assert "fn_42" in str(err)
        assert err.function_id == "fn_42"

    def test_error_code(self) -> None:
        err = FunctionNotFoundError("fn_1")
        assert err.code is ErrorCode.NOT_FOUND


class TestScriptExecutionError:
    def test_message_includes_id(self) -> None:
        err = ScriptExecutionError("exec_1", "timeout")
        assert "exec_1" in str(err)
        assert "timeout" in str(err)
        assert err.execution_id == "exec_1"


class TestScriptTimeoutError:
    def test_message_includes_details(self) -> None:
        err = ScriptTimeoutError("fn_1", 30.0)
        assert "fn_1" in str(err)
        assert "30" in str(err)
        assert err.function_id == "fn_1"
        assert err.timeout_seconds == 30.0

    def test_error_code(self) -> None:
        err = ScriptTimeoutError("fn_1", 30.0)
        assert err.code is ErrorCode.PROVIDER_TIMEOUT


class TestSandboxViolationError:
    def test_message(self) -> None:
        err = SandboxViolationError("import not allowed: os")
        assert "import not allowed" in str(err)

    def test_error_code(self) -> None:
        err = SandboxViolationError("test")
        assert err.code is ErrorCode.POLICY_VIOLATION


class TestExceptionHierarchy:
    def test_all_exceptions_inherit_script_error(self) -> None:
        assert issubclass(FunctionNotFoundError, ScriptError)
        assert issubclass(ScriptExecutionError, ScriptError)
        assert issubclass(ScriptTimeoutError, ScriptError)
        assert issubclass(SandboxViolationError, ScriptError)
