"""JSON Schema Service — schema document management, validation, and lifecycle."""

from __future__ import annotations

from eaip.jsonschema.events import (
    SchemaCreated,
    SchemaDeprecated,
    SchemaUpdated,
    ValidationPerformed,
)
from eaip.jsonschema.exceptions import (
    SchemaNotFoundError,
    SchemaServiceError,
)
from eaip.jsonschema.health import SchemaHealthCheck
from eaip.jsonschema.integration import SchemaRuntimeModule
from eaip.jsonschema.models import (
    SchemaConfig,
    SchemaDocument,
    SchemaStatus,
    SchemaValidationResult,
)
from eaip.jsonschema.service import JSONSchemaService

__all__ = [
    "JSONSchemaService",
    "SchemaConfig",
    "SchemaCreated",
    "SchemaDeprecated",
    "SchemaDocument",
    "SchemaHealthCheck",
    "SchemaNotFoundError",
    "SchemaRuntimeModule",
    "SchemaServiceError",
    "SchemaStatus",
    "SchemaUpdated",
    "SchemaValidationResult",
    "ValidationPerformed",
]
