"""Cluster Coordination & High Availability — node management, leader election, monitoring."""

from __future__ import annotations

from eaip.cluster.coordinator import ClusterCoordinator
from eaip.cluster.election import LeaderElection
from eaip.cluster.events import (
    ClusterEvent,
    ClusterStateChanged,
    HeartbeatMissed,
    LeaderElected,
    NodeJoined,
    NodeLeft,
    NodePromoted,
)
from eaip.cluster.exceptions import (
    ClusterError,
    ClusterQuorumLostError,
    LeaderNotAvailableError,
    MembershipError,
    NodeNotFoundError,
)
from eaip.cluster.health import ClusterHealthCheck
from eaip.cluster.integration import ClusterRuntimeModule
from eaip.cluster.membership import HeartbeatMonitor, MembershipManager
from eaip.cluster.models import (
    ChangeType,
    ClusterConfig,
    ClusterNode,
    ClusterState,
    Heartbeat,
    MembershipChange,
    NodeRole,
    NodeStatus,
)

__all__ = [
    "ChangeType",
    "ClusterConfig",
    "ClusterCoordinator",
    "ClusterError",
    "ClusterEvent",
    "ClusterHealthCheck",
    "ClusterNode",
    "ClusterQuorumLostError",
    "ClusterRuntimeModule",
    "ClusterState",
    "ClusterStateChanged",
    "Heartbeat",
    "HeartbeatMissed",
    "HeartbeatMonitor",
    "LeaderElected",
    "LeaderElection",
    "LeaderNotAvailableError",
    "MembershipChange",
    "MembershipError",
    "MembershipManager",
    "NodeJoined",
    "NodeLeft",
    "NodeNotFoundError",
    "NodePromoted",
    "NodeRole",
    "NodeStatus",
]
