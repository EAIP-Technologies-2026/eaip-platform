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


class PolicyViolationError(EAIPError):
    """Raised when a request is denied by the authorization manager."""

    default_code = ErrorCode.POLICY_VIOLATION


__all__ = [
    "ConfigurationError",
    "DependencyCycleError",
    "DependencyError",
    "DuplicateRegistrationError",
    "LifecycleError",
    "NotFoundError",
    "PluginContractViolationError",
    "PluginError",
    "PolicyViolationError",
    "RegistryError",
    "RegistryTypeMismatchError",
    "SerializationError",
    "ValidationError",
]
