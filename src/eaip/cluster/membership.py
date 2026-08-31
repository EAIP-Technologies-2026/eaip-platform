"""Cluster membership management and heartbeat monitoring."""

from __future__ import annotations

import asyncio
import contextlib

from eaip.cluster.exceptions import (
    MembershipError,
    NodeNotFoundError,
)
from eaip.cluster.models import (
    ClusterConfig,
    ClusterNode,
    NodeStatus,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class MembershipManager:
    """Manages cluster membership — tracks nodes, handles join/leave operations."""

    def __init__(self, config: ClusterConfig) -> None:
        """Initialize with cluster configuration."""
        self._config = config
        self._nodes: dict[str, ClusterNode] = {}
        self._log = get_logger("eaip.cluster.membership")

    @property
    def nodes(self) -> tuple[ClusterNode, ...]:
        """Return all registered nodes."""
        return tuple(self._nodes.values())

    @property
    def node_count(self) -> int:
        """Return the number of registered nodes."""
        return len(self._nodes)

    def add_node(self, node: ClusterNode) -> None:
        """Register a new node in the cluster."""
        if node.node_id in self._nodes:
            raise MembershipError(f"node already exists: {node.node_id}")
        if self.node_count >= self._config.max_nodes:
            raise MembershipError("cluster at maximum capacity")
        self._nodes[node.node_id] = node

    def remove_node(self, node_id: str) -> ClusterNode:
        """Remove a node from the cluster and return it."""
        node = self._nodes.pop(node_id, None)
        if node is None:
            raise NodeNotFoundError(node_id)
        return node

    def get_node(self, node_id: str) -> ClusterNode:
        """Look up a node by id."""
        node = self._nodes.get(node_id)
        if node is None:
            raise NodeNotFoundError(node_id)
        return node

    def update_heartbeat(
        self,
        node_id: str,
        status: NodeStatus = NodeStatus.ONLINE,
        _load: float = 0.0,
    ) -> None:
        """Update the last heartbeat timestamp for a node."""
        node = self.get_node(node_id)
        self._nodes[node_id] = ClusterNode(
            node_id=node.node_id,
            host=node.host,
            port=node.port,
            role=node.role,
            status=status,
            started_at=node.started_at,
            last_heartbeat=utc_now(),
            metadata=node.metadata,
        )


class HeartbeatMonitor:
    """Periodic heartbeat checking with timeout detection."""

    _MAX_MISSED_BEFORE_OFFLINE: int = 3

    def __init__(self, membership: MembershipManager, config: ClusterConfig) -> None:
        """Initialize with membership manager and cluster config."""
        self._membership = membership
        self._config = config
        self._missed: dict[str, int] = {}
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._log = get_logger("eaip.cluster.heartbeat")

    @property
    def is_running(self) -> bool:
        """Return True if the monitor is active."""
        return self._running

    @property
    def missed_count(self) -> dict[str, int]:
        """Return a copy of the missed heartbeat counts."""
        return dict(self._missed)

    async def start(self) -> None:
        """Start the periodic heartbeat monitoring loop."""
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the heartbeat monitoring loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _run(self) -> None:
        while self._running:
            await asyncio.sleep(self._config.heartbeat_interval_seconds)
            self._check_heartbeats()

    def _check_heartbeats(self) -> None:
        now = utc_now()
        timeout = self._config.election_timeout_seconds
        for node in self._membership.nodes:
            elapsed = (now - node.last_heartbeat).total_seconds()
            if elapsed > timeout:
                missed = self._missed.get(node.node_id, 0) + 1
                self._missed[node.node_id] = missed
                if missed >= self._MAX_MISSED_BEFORE_OFFLINE:
                    self._log.warning(
                        "node.marked.offline",
                        node_id=node.node_id,
                    )
            else:
                self._missed.pop(node.node_id, None)


__all__ = ["HeartbeatMonitor", "MembershipManager"]
