"""Domain-level exceptions used by the Platform Foundation."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ConfigurationError(EAIPError):
    """Raised when configuration is missing, malformed, or contradictory."""

    default_code = ErrorCode.CONFIGURATION_INVALID


class ValidationError(EAIPError):
    """Raised when input fails declarative validation."""

    default_code = ErrorCode.VALIDATION_FAILED


class NotFoundError(EAIPError):
    """Raised when a requested entity does not exist."""

    default_code = ErrorCode.NOT_FOUND


class DependencyError(EAIPError):
    """Raised when a required dependency cannot be resolved.

    Distinct subtypes describe the *kind* of failure (missing vs. cyclic).
    """

    default_code = ErrorCode.DEPENDENCY_MISSING


class DependencyCycleError(DependencyError):
    """Raised when a cyclic dependency is detected at resolution time."""

    default_code = ErrorCode.DEPENDENCY_CYCLE


class LifecycleError(EAIPError):
    """Raised when an operation is performed in the wrong lifecycle phase."""

    default_code = ErrorCode.LIFECYCLE_FORBIDDEN


class RegistryError(EAIPError):
    """Base for registry-related failures."""

    default_code = ErrorCode.REGISTRY_DUPLICATE


class DuplicateRegistrationError(RegistryError):
    """Raised when registering a name/key that is already present."""

    default_code = ErrorCode.REGISTRY_DUPLICATE


class RegistryTypeMismatchError(RegistryError):
    """Raised when a registered value violates the registry's declared type."""

    default_code = ErrorCode.REGISTRY_TYPE_MISMATCH


class PluginError(EAIPError):
    """Base for plugin-related failures."""

    default_code = ErrorCode.PLUGIN_LOAD_FAILED


class PluginContractViolationError(PluginError):
    """Raised when a plugin fails its declared contract checks."""

    default_code = ErrorCode.PLUGIN_CONTRACT_VIOLATION


class SerializationError(EAIPError):
    """Raised on JSON / binary (de)serialisation failures."""

    default_code = ErrorCode.SERIALIZATION_FAILED


class PipelineError(EAIPError):
    """Base for pipeline execution failures."""

    default_code = ErrorCode.PIPELINE_EXECUTION_FAILED


class SchedulerError(EAIPError):
    """Base for scheduler-related failures."""

    default_code = ErrorCode.SCHEDULER_TASK_FAILED


class CommandHandlerNotFoundError(EAIPError):
    """Raised when no handler is registered for a command type."""

    default_code = ErrorCode.COMMAND_HANDLER_NOT_FOUND


class CommandValidationError(EAIPError):
    """Raised when a command fails validation."""

    default_code = ErrorCode.COMMAND_VALIDATION_FAILED


class CommandRetryExhaustedError(EAIPError):
    """Raised when all retry attempts for a command have been exhausted."""

    default_code = ErrorCode.COMMAND_RETRY_EXHAUSTED


class QueryHandlerNotFoundError(EAIPError):
    """Raised when no handler is registered for a query type."""

    default_code = ErrorCode.QUERY_HANDLER_NOT_FOUND


class QueryCacheError(EAIPError):
    """Raised when a cache operation fails."""

    default_code = ErrorCode.QUERY_CACHE_ERROR


class WorkerPoolExhaustedError(EAIPError):
    """Raised when submitting a task to a stopped or full worker pool."""

    default_code = ErrorCode.WORKER_POOL_EXHAUSTED


class WorkerTaskFailedError(EAIPError):
    """Raised when a background worker task raises an unhandled exception.

    This error is returned when the caller requested error propagation.
    """

    default_code = ErrorCode.WORKER_TASK_FAILED


__all__ = [
    "CommandHandlerNotFoundError",
    "CommandRetryExhaustedError",
    "CommandValidationError",
    "ConfigurationError",
    "DependencyCycleError",
    "DependencyError",
    "DuplicateRegistrationError",
    "LifecycleError",
    "NotFoundError",
    "PipelineError",
    "PluginContractViolationError",
    "PluginError",
    "QueryCacheError",
    "QueryHandlerNotFoundError",
    "RegistryError",
    "RegistryTypeMismatchError",
    "SchedulerError",
    "SerializationError",
    "ValidationError",
    "WorkerPoolExhaustedError",
    "WorkerTaskFailedError",
]
