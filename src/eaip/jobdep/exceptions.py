"""Exception hierarchy for the job dependency manager."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class JobDepError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class NodeNotFoundError(JobDepError):
    default_code = ErrorCode.NOT_FOUND

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        super().__init__(f"node not found: {node_id!r}")


class CircularDependencyError(JobDepError):
    default_code = ErrorCode.DEPENDENCY_CYCLE

    def __init__(self, source_id: str, target_id: str) -> None:
        self.source_id = source_id
        self.target_id = target_id
        super().__init__(f"circular dependency detected: {source_id!r} -> {target_id!r}")


__all__ = [
    "CircularDependencyError",
    "JobDepError",
    "NodeNotFoundError",
]
