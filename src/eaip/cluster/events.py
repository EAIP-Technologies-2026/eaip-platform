"""Domain events for cluster coordination."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class NodeJoined(DomainEvent):
    """Published when a node joins the cluster."""

    event_type: ClassVar[str] = "eaip.cluster.node.joined"
    node_id: str = ""
    host: str = ""
    port: int = 0
    role: str = ""


class NodeLeft(DomainEvent):
    """Published when a node leaves the cluster."""

    event_type: ClassVar[str] = "eaip.cluster.node.left"
    node_id: str = ""
    reason: str = ""


class NodePromoted(DomainEvent):
    """Published when a node is promoted to a new role."""

    event_type: ClassVar[str] = "eaip.cluster.node.promoted"
    node_id: str = ""
    new_role: str = ""


class LeaderElected(DomainEvent):
    """Published when a leader is elected for a term."""

    event_type: ClassVar[str] = "eaip.cluster.leader.elected"
    leader_id: str = ""
    term: int = 0


class HeartbeatMissed(DomainEvent):
    """Published when a node misses too many heartbeats."""

    event_type: ClassVar[str] = "eaip.cluster.heartbeat.missed"
    node_id: str = ""
    missed_count: int = 0


class ClusterStateChanged(DomainEvent):
    """Published when the cluster transitions to a new state."""

    event_type: ClassVar[str] = "eaip.cluster.state.changed"
    previous_state: str = ""
    new_state: str = ""


ClusterEvent = (
    NodeJoined | NodeLeft | NodePromoted | LeaderElected | HeartbeatMissed | ClusterStateChanged
)


__all__ = [
    "ClusterEvent",
    "ClusterStateChanged",
    "HeartbeatMissed",
    "LeaderElected",
    "NodeJoined",
    "NodeLeft",
    "NodePromoted",
]
