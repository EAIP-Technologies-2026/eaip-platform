"""Model Registry — versioned model storage, discovery, and lifecycle management."""

from __future__ import annotations

from eaip.modelreg.events import (
    ModelArchived,
    ModelDeprecated,
    ModelRegistered,
    ModelVersioned,
)
from eaip.modelreg.exceptions import (
    ModelNotFoundError,
    ModelRegistryError,
    ModelVersionConflictError,
)
from eaip.modelreg.health import ModelRegistryHealthCheck
from eaip.modelreg.integration import ModelRegistryRuntimeModule
from eaip.modelreg.models import (
    ModelArtifact,
    ModelRegistryConfig,
    ModelRegistryEntry,
    ModelVersion,
)

__all__ = [
    "ModelArchived",
    "ModelArtifact",
    "ModelDeprecated",
    "ModelNotFoundError",
    "ModelRegistered",
    "ModelRegistryConfig",
    "ModelRegistryEntry",
    "ModelRegistryError",
    "ModelRegistryHealthCheck",
    "ModelRegistryRuntimeModule",
    "ModelVersion",
    "ModelVersionConflictError",
    "ModelVersioned",
]
