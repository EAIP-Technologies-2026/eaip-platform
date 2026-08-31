"""Cluster domain models — ClusterNode, ClusterConfig, ClusterState, Heartbeat, MembershipChange."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class NodeRole(StrEnum):
    """Role a node can assume in the cluster."""

    LEADER = "leader"
    FOLLOWER = "follower"
    OBSERVER = "observer"


class NodeStatus(StrEnum):
    """Operational status of a cluster node."""

    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


class ChangeType(StrEnum):
    """Type of membership change operation."""

    JOIN = "join"
    LEAVE = "leave"
    PROMOTE = "promote"
    DEMOTE = "demote"


class ClusterNode(BaseModel):
    """A single node participating in the cluster."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    node_id: str
    host: str
    port: int
    role: NodeRole
    status: NodeStatus = NodeStatus.ONLINE
    started_at: datetime = Field(default_factory=utc_now)
    last_heartbeat: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClusterConfig(BaseModel):
    """Configuration parameters for the cluster."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    cluster_name: str
    heartbeat_interval_seconds: int = 5
    election_timeout_seconds: int = 30
    min_nodes: int = 1
    max_nodes: int = 10


class ClusterState(BaseModel):
    """Snapshot of the cluster's state at a point in time."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    leader_id: str | None = None
    nodes: tuple[ClusterNode, ...] = Field(default_factory=tuple)
    term: int = 0
    last_applied: int = 0
    state: str = "follower"


class Heartbeat(BaseModel):
    """Heartbeat signal sent from a node to indicate liveness."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    node_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    load: float = 0.0
    status: NodeStatus = NodeStatus.ONLINE


class MembershipChange(BaseModel):
    """Record of a membership change event in the cluster."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    node_id: str
    change_type: ChangeType
    timestamp: datetime = Field(default_factory=utc_now)
    reason: str | None = None


__all__ = [
    "ChangeType",
    "ClusterConfig",
    "ClusterNode",
    "ClusterState",
    "Heartbeat",
    "MembershipChange",
    "NodeRole",
    "NodeStatus",
]
