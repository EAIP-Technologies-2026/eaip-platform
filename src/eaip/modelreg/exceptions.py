"""Exception hierarchy for the model registry."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ModelRegistryError(EAIPError):
    """Base exception for model registry errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ModelNotFoundError(ModelRegistryError):
    """Raised when a model is not found in the registry."""

    default_code = ErrorCode.MODEL_NOT_FOUND


class ModelVersionConflictError(ModelRegistryError):
    """Raised when a version conflict occurs in the registry."""

    default_code = ErrorCode.REGISTRY_DUPLICATE


__all__ = [
    "ModelNotFoundError",
    "ModelRegistryError",
    "ModelVersionConflictError",
]
