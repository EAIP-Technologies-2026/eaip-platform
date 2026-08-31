"""Exception hierarchy for cluster coordination."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class ClusterError(EAIPError):
    """Base exception for all cluster-related errors."""

    default_code = ErrorCode.UNKNOWN
    default_severity = ErrorSeverity.ERROR


class NodeNotFoundError(ClusterError):
    """Raised when a requested node does not exist in the cluster."""

    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING

    def __init__(self, node_id: str) -> None:
        """Initialize with the missing node id."""
        self.node_id = node_id
        super().__init__(f"cluster node not found: {node_id!r}")


class LeaderNotAvailableError(ClusterError):
    """Raised when no leader is currently available."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE
    default_severity = ErrorSeverity.ERROR

    def __init__(self, message: str = "no leader available") -> None:
        """Initialize with an optional custom message."""
        super().__init__(message)


class ClusterQuorumLostError(ClusterError):
    """Raised when the cluster loses quorum."""

    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.CRITICAL

    def __init__(self, node_count: int, quorum_required: int) -> None:
        """Initialize with node count and quorum required."""
        self.node_count = node_count
        self.quorum_required = quorum_required
        super().__init__(f"cluster quorum lost: {node_count} nodes, {quorum_required} required")


class MembershipError(ClusterError):
    """Raised when a membership operation fails."""

    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.ERROR

    def __init__(self, message: str) -> None:
        """Initialize with a descriptive message."""
        super().__init__(message)


__all__ = [
    "ClusterError",
    "ClusterQuorumLostError",
    "LeaderNotAvailableError",
    "MembershipError",
    "NodeNotFoundError",
]
