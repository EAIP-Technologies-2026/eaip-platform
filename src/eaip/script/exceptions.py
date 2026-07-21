"""Script runtime exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ScriptError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class FunctionNotFoundError(ScriptError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, function_id: str) -> None:
        self.function_id = function_id
        super().__init__(f"script function not found: {function_id!r}")


class ScriptExecutionError(ScriptError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, execution_id: str, message: str) -> None:
        self.execution_id = execution_id
        super().__init__(f"script execution {execution_id!r} failed: {message}")


class ScriptTimeoutError(ScriptError):
    default_code: ErrorCode = ErrorCode.PROVIDER_TIMEOUT

    def __init__(self, function_id: str, timeout_seconds: float) -> None:
        self.function_id = function_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"script function {function_id!r} timed out after {timeout_seconds}s")


class SandboxViolationError(ScriptError):
    default_code: ErrorCode = ErrorCode.POLICY_VIOLATION

    def __init__(self, message: str) -> None:
        super().__init__(f"sandbox violation: {message}")


__all__ = [
    "FunctionNotFoundError",
    "SandboxViolationError",
    "ScriptError",
    "ScriptExecutionError",
    "ScriptTimeoutError",
]
