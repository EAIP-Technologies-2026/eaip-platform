"""Platform-wide exception hierarchy.

All EAIP exceptions inherit from :class:`EAIPError`, carry a stable
``error_code``, and accept a structured ``context`` dictionary for
observability. This guarantees consistent error reporting across every
component without forcing each caller to invent its own conventions.
"""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity
from eaip.exceptions.domain import (
    ConfigurationError,
    DependencyError,
    LifecycleError,
    NotFoundError,
    PluginError,
    PolicyViolationError,
    RegistryError,
    SerializationError,
    ValidationError,
)

__all__ = [
    "ConfigurationError",
    "DependencyError",
    "EAIPError",
    "ErrorCode",
    "ErrorSeverity",
    "LifecycleError",
    "NotFoundError",
    "PluginError",
    "PolicyViolationError",
    "RegistryError",
    "SerializationError",
    "ValidationError",
]
