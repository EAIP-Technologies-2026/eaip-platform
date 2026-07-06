"""Runtime exception types.

Extends the base exception hierarchy with Runtime-Kernel-specific codes.
"""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class KernelError(EAIPError):
    """Base for all runtime-kernel failures."""

    default_code = ErrorCode.RUNTIME_ERROR


class ModuleLoadError(KernelError):
    """Raised when a :class:`~eaip.runtime.module.RuntimeModule` cannot be loaded."""

    default_code = ErrorCode.MODULE_LOAD_FAILED


class ModuleActivationError(KernelError):
    """Raised when a module fails to start or stop."""

    default_code = ErrorCode.MODULE_ACTIVATION_FAILED


class DependencyResolutionError(KernelError):
    """Raised when the dependency graph cannot be satisfied (missing or cyclic)."""

    default_code = ErrorCode.RUNTIME_DEPENDENCY_ERROR


class RuntimeContextError(KernelError):
    """Raised when a :class:`~eaip.runtime.context.RuntimeContext` operation fails."""

    default_code = ErrorCode.RUNTIME_CONTEXT_ERROR


__all__ = [
    "DependencyResolutionError",
    "KernelError",
    "ModuleActivationError",
    "ModuleLoadError",
    "RuntimeContextError",
]
