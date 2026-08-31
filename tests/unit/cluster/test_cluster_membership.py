"""Tests for MembershipManager and HeartbeatMonitor."""

from __future__ import annotations

from datetime import timedelta

import pytest

from eaip.cluster.exceptions import (
    MembershipError,
    NodeNotFoundError,
)
from eaip.cluster.membership import (
    HeartbeatMonitor,
    MembershipManager,
)
from eaip.cluster.models import (
    ClusterConfig,
    ClusterNode,
    NodeRole,
    NodeStatus,
)
from eaip.shared.time import utc_now


@pytest.fixture
def config() -> ClusterConfig:
    return ClusterConfig(
        cluster_name="test-cluster",
        heartbeat_interval_seconds=1,
        election_timeout_seconds=5,
        max_nodes=3,
    )


@pytest.fixture
def node_a() -> ClusterNode:
    return ClusterNode(
        node_id="node_a",
        host="192.168.1.1",
        port=8000,
        role=NodeRole.FOLLOWER,
    )


@pytest.fixture
def node_b() -> ClusterNode:
    return ClusterNode(
        node_id="node_b",
        host="192.168.1.2",
        port=8000,
        role=NodeRole.FOLLOWER,
    )


class TestMembershipManager:
    def test_initial_state(self, config: ClusterConfig) -> None:
        mgr = MembershipManager(config)
        assert mgr.node_count == 0
        assert mgr.nodes == ()

    def test_add_node(
        self,
        config: ClusterConfig,
        node_a: ClusterNode,
    ) -> None:
        mgr = MembershipManager(config)
        mgr.add_node(node_a)
        assert mgr.node_count == 1
        assert mgr.get_node("node_a") == node_a

    def test_add_duplicate_node(
        self,
        config: ClusterConfig,
        node_a: ClusterNode,
    ) -> None:
        mgr = MembershipManager(config)
        mgr.add_node(node_a)
        with pytest.raises(MembershipError):
            mgr.add_node(node_a)

    def test_add_beyond_max(
        self,
        config: ClusterConfig,
        node_a: ClusterNode,
        node_b: ClusterNode,
    ) -> None:
        mgr = MembershipManager(config)
        mgr.add_node(node_a)
        mgr.add_node(node_b)
        node_c = ClusterNode(
            node_id="node_c",
            host="192.168.1.3",
            port=8000,
            role=NodeRole.FOLLOWER,
        )
        mgr.add_node(node_c)
        node_d = ClusterNode(
            node_id="node_d",
            host="192.168.1.4",
            port=8000,
            role=NodeRole.FOLLOWER,
        )
        with pytest.raises(MembershipError):
            mgr.add_node(node_d)

    def test_remove_node(
        self,
        config: ClusterConfig,
        node_a: ClusterNode,
    ) -> None:
        mgr = MembershipManager(config)
        mgr.add_node(node_a)
        removed = mgr.remove_node("node_a")
        assert removed == node_a
        assert mgr.node_count == 0

    def test_remove_nonexistent_node(self, config: ClusterConfig) -> None:
        mgr = MembershipManager(config)
        with pytest.raises(NodeNotFoundError):
            mgr.remove_node("nonexistent")

    def test_get_node(
        self,
        config: ClusterConfig,
        node_a: ClusterNode,
    ) -> None:
        mgr = MembershipManager(config)
        mgr.add_node(node_a)
        assert mgr.get_node("node_a") == node_a

    def test_get_node_not_found(self, config: ClusterConfig) -> None:
        mgr = MembershipManager(config)
        with pytest.raises(NodeNotFoundError):
            mgr.get_node("nonexistent")

    def test_update_heartbeat(
        self,
        config: ClusterConfig,
        node_a: ClusterNode,
    ) -> None:
        mgr = MembershipManager(config)
        mgr.add_node(node_a)
        mgr.update_heartbeat(
            "node_a",
            status=NodeStatus.DEGRADED,
        )
        updated = mgr.get_node("node_a")
        assert updated.status is NodeStatus.DEGRADED
        assert updated.last_heartbeat != node_a.last_heartbeat

    def test_update_heartbeat_not_found(self, config: ClusterConfig) -> None:
        mgr = MembershipManager(config)
        with pytest.raises(NodeNotFoundError):
            mgr.update_heartbeat("nonexistent")

    def test_nodes_property(
        self,
        config: ClusterConfig,
        node_a: ClusterNode,
        node_b: ClusterNode,
    ) -> None:
        mgr = MembershipManager(config)
        mgr.add_node(node_a)
        mgr.add_node(node_b)
        assert len(mgr.nodes) == 2
        assert node_a in mgr.nodes
        assert node_b in mgr.nodes


class TestHeartbeatMonitor:
    async def test_initial_state(self, config: ClusterConfig) -> None:
        mgr = MembershipManager(config)
        monitor = HeartbeatMonitor(mgr, config)
        assert monitor.is_running is False
        assert monitor.missed_count == {}

    async def test_start_stop(self, config: ClusterConfig) -> None:
        mgr = MembershipManager(config)
        monitor = HeartbeatMonitor(mgr, config)
        await monitor.start()
        assert monitor.is_running is True
        await monitor.stop()
        assert monitor.is_running is False

    async def test_missed_count(self, config: ClusterConfig) -> None:
        mgr = MembershipManager(config)
        old_time = utc_now() - timedelta(seconds=60)
        node = ClusterNode(
            node_id="node_a",
            host="192.168.1.1",
            port=8000,
            role=NodeRole.FOLLOWER,
            last_heartbeat=old_time,
        )
        mgr.add_node(node)
        monitor = HeartbeatMonitor(mgr, config)
        monitor._check_heartbeats()
        monitor._check_heartbeats()
        assert monitor.missed_count.get("node_a", 0) >= 1
