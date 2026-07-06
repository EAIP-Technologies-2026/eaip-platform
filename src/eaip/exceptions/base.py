"""Base exception class shared by every EAIP exception."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Self


class ErrorSeverity(StrEnum):
    """Severity classification used by observability tooling."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCode(StrEnum):
    """Stable, machine-readable error codes.

    Codes follow ``EAIP-XXXX`` where ``XXXX`` is a zero-padded sequence.
    Codes are part of the public API and **must not** be removed or
    renumbered; deprecated codes are kept and marked.
    """

    UNKNOWN = "EAIP-0000"
    CONFIGURATION_INVALID = "EAIP-0001"
    VALIDATION_FAILED = "EAIP-0002"
    NOT_FOUND = "EAIP-0003"
    DEPENDENCY_MISSING = "EAIP-0004"
    DEPENDENCY_CYCLE = "EAIP-0005"
    LIFECYCLE_FORBIDDEN = "EAIP-0006"
    REGISTRY_DUPLICATE = "EAIP-0007"
    REGISTRY_TYPE_MISMATCH = "EAIP-0008"
    PLUGIN_LOAD_FAILED = "EAIP-0009"
    PLUGIN_CONTRACT_VIOLATION = "EAIP-0010"
    SERIALIZATION_FAILED = "EAIP-0011"
    # Runtime Kernel — EP-0002 Sprint 1
    RUNTIME_ERROR = "EAIP-0012"
    MODULE_LOAD_FAILED = "EAIP-0013"
    MODULE_ACTIVATION_FAILED = "EAIP-0014"
    RUNTIME_DEPENDENCY_ERROR = "EAIP-0015"
    RUNTIME_CONTEXT_ERROR = "EAIP-0016"
    # Runtime Kernel Core — EP-0002 Sprint 3
    KERNEL_INITIALIZATION_FAILED = "EAIP-0017"
    KERNEL_START_FAILED = "EAIP-0018"
    BOOTSTRAP_HOOK_FAILED = "EAIP-0019"
    # Runtime Pipeline & Scheduler — EP-0002 Sprint 4
    PIPELINE_EXECUTION_FAILED = "EAIP-0020"
    PIPELINE_MIDDLEWARE_FAILED = "EAIP-0021"
    SCHEDULER_TASK_FAILED = "EAIP-0022"
    SCHEDULER_CRON_INVALID = "EAIP-0023"
    # Runtime Command / Query Bus — EP-0002 Sprint 4
    COMMAND_HANDLER_NOT_FOUND = "EAIP-0024"
    COMMAND_VALIDATION_FAILED = "EAIP-0025"
    COMMAND_RETRY_EXHAUSTED = "EAIP-0026"
    QUERY_HANDLER_NOT_FOUND = "EAIP-0027"
    QUERY_CACHE_ERROR = "EAIP-0028"
    # Runtime Workers & Cache — Bundle-005
    WORKER_POOL_EXHAUSTED = "EAIP-0029"
    WORKER_TASK_FAILED = "EAIP-0030"


class EAIPError(Exception):
    """The root exception type for the platform.

    Parameters
    ----------
    message:
        Human-readable, English-language description. Avoid embedding values
        that should be machine-parsed; place those in ``context`` instead.
    code:
        A stable :class:`ErrorCode`. Defaults to :attr:`ErrorCode.UNKNOWN`.
    context:
        Optional structured metadata attached to the error. Values must be
        JSON-serialisable (strings, numbers, bools, lists, dicts, ``None``).
    cause:
        The underlying exception, if any. Stored on ``__cause__``.
    severity:
        Classification used by logging/observability. Defaults to ERROR.
    """

    default_code: ErrorCode = ErrorCode.UNKNOWN
    default_severity: ErrorSeverity = ErrorSeverity.ERROR

    __slots__ = ("code", "context", "severity")

    def __init__(
        self,
        message: str,
        *,
        code: ErrorCode | None = None,
        context: Mapping[str, Any] | None = None,
        cause: BaseException | None = None,
        severity: ErrorSeverity | None = None,
    ) -> None:
        super().__init__(message)
        self.code: ErrorCode = code or self.default_code
        self.context: dict[str, Any] = dict(context) if context else {}
        self.severity: ErrorSeverity = severity or self.default_severity
        if cause is not None:
            self.__cause__ = cause

    def with_context(self, **extra: Any) -> Self:
        """Return a copy of this error with additional context merged in."""
        merged = {**self.context, **extra}
        clone = type(self)(
            str(self),
            code=self.code,
            context=merged,
            severity=self.severity,
        )
        clone.__cause__ = self.__cause__
        return clone

    def to_dict(self) -> dict[str, Any]:
        """Render the error as a JSON-safe dictionary."""
        return {
            "type": type(self).__name__,
            "code": str(self.code),
            "severity": str(self.severity),
            "message": str(self),
            "context": dict(self.context),
            "cause": repr(self.__cause__) if self.__cause__ else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"{type(self).__name__}(code={self.code!s}, "
            f"message={str(self)!r}, context={self.context!r})"
        )


__all__ = ["EAIPError", "ErrorCode", "ErrorSeverity"]
