"""Knowledge Graph exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class GraphError(EAIPError):
    """Base exception for Knowledge Graph errors."""

    default_code = ErrorCode.UNKNOWN


class EntityNotFoundError(GraphError):
    """Raised when an entity is not found in the graph."""

    default_code = ErrorCode.NOT_FOUND


class RelationshipNotFoundError(GraphError):
    """Raised when a relationship is not found in the graph."""

    default_code = ErrorCode.NOT_FOUND


class GraphQueryError(GraphError):
    """Raised when a graph query fails."""

    default_code = ErrorCode.UNKNOWN


class GraphTraversalError(GraphError):
    """Raised when a graph traversal fails."""

    default_code = ErrorCode.UNKNOWN


class EntityValidationError(GraphError):
    """Raised when entity data fails validation."""

    default_code = ErrorCode.VALIDATION_FAILED


__all__ = [
    "EntityNotFoundError",
    "EntityValidationError",
    "GraphError",
    "GraphQueryError",
    "GraphTraversalError",
    "RelationshipNotFoundError",
]
