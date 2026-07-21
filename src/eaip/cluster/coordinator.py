"""High-level cluster coordinator — node registration, health monitoring, leader election."""

from __future__ import annotations

from eaip.cluster.election import LeaderElection
from eaip.cluster.membership import (
    HeartbeatMonitor,
    MembershipManager,
)
from eaip.cluster.models import ClusterConfig, ClusterNode
from eaip.logging.context import get_logger


class ClusterCoordinator:
    """Coordinates cluster operations: registration, monitoring, election, state management."""

    def __init__(self, config: ClusterConfig | None = None) -> None:
        """Initialize the coordinator with optional config, creating subsystems as needed."""
        self._config = config or ClusterConfig(cluster_name="default")
        self._membership = MembershipManager(self._config)
        self._election = LeaderElection(node_id="", membership=self._membership)
        self._heartbeat_monitor = HeartbeatMonitor(self._membership, self._config)
        self._log = get_logger("eaip.cluster.coordinator")

    @property
    def config(self) -> ClusterConfig:
        """Return the cluster configuration."""
        return self._config

    @property
    def membership(self) -> MembershipManager:
        """Return the membership manager."""
        return self._membership

    @property
    def leader_id(self) -> str | None:
        """Return the current leader id, or None."""
        return self._election.leader_id

    @property
    def is_leader(self) -> bool:
        """Return True if this node is the leader."""
        return self._election.is_leader

    async def register_node(self, node: ClusterNode) -> None:
        """Register a new node in the cluster."""
        self._membership.add_node(node)

    async def unregister_node(self, node_id: str) -> ClusterNode:
        """Remove a node from the cluster and return it."""
        return self._membership.remove_node(node_id)

    async def start(self) -> None:
        """Start the heartbeat monitor."""
        await self._heartbeat_monitor.start()

    async def stop(self) -> None:
        """Stop the heartbeat monitor."""
        await self._heartbeat_monitor.stop()


__all__ = ["ClusterCoordinator"]
