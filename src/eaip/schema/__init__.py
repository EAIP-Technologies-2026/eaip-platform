"""Schema Registry — schema management, validation, evolution, and compatibility checking.

Provides :class:`SchemaRegistry` for CRUD operations on schema definitions and
versions, :class:`SchemaValidator` for validating data against registered schemas,
and :class:`CompatibilityChecker` for checking backward/forward/full compatibility
between schema versions.
"""

from __future__ import annotations

from eaip.schema.compatibility import CompatibilityChecker
from eaip.schema.events import (
    SchemaCompatibilityChecked,
    SchemaDeprecated,
    SchemaRegistered,
    SchemaSuperseded,
    SchemaValidated,
    SchemaVersionCreated,
)
from eaip.schema.exceptions import (
    CompatibilityError,
    SchemaError,
    SchemaNotFoundError,
    SchemaValidationError,
    SchemaVersionNotFoundError,
)
from eaip.schema.health import SchemaHealthCheck
from eaip.schema.integration import SchemaRuntimeModule
from eaip.schema.models import (
    CompatibilityResult,
    CompatibilityType,
    SchemaConfig,
    SchemaDefinition,
    SchemaStatus,
    SchemaType,
    SchemaValidationResult,
    SchemaVersion,
)
from eaip.schema.registry import SchemaRegistry
from eaip.schema.validation import SchemaValidator

__all__ = [
    "CompatibilityChecker",
    "CompatibilityError",
    "CompatibilityResult",
    "CompatibilityType",
    "SchemaCompatibilityChecked",
    "SchemaConfig",
    "SchemaDefinition",
    "SchemaDeprecated",
    "SchemaError",
    "SchemaHealthCheck",
    "SchemaNotFoundError",
    "SchemaRegistered",
    "SchemaRegistry",
    "SchemaRuntimeModule",
    "SchemaStatus",
    "SchemaSuperseded",
    "SchemaType",
    "SchemaValidated",
    "SchemaValidationError",
    "SchemaValidationResult",
    "SchemaValidationResult",
    "SchemaValidator",
    "SchemaVersion",
    "SchemaVersionCreated",
    "SchemaVersionNotFoundError",
]
