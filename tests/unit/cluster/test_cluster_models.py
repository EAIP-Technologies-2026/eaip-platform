"""Tests for Cluster domain models."""

from __future__ import annotations

from datetime import datetime

import pytest

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


class TestNodeRole:
    def test_values(self) -> None:
        assert NodeRole.LEADER == "leader"
        assert NodeRole.FOLLOWER == "follower"
        assert NodeRole.OBSERVER == "observer"

    def test_valid_members(self) -> None:
        assert len(NodeRole) == 3


class TestNodeStatus:
    def test_values(self) -> None:
        assert NodeStatus.ONLINE == "online"
        assert NodeStatus.OFFLINE == "offline"
        assert NodeStatus.DEGRADED == "degraded"

    def test_valid_members(self) -> None:
        assert len(NodeStatus) == 3


class TestChangeType:
    def test_values(self) -> None:
        assert ChangeType.JOIN == "join"
        assert ChangeType.LEAVE == "leave"
        assert ChangeType.PROMOTE == "promote"
        assert ChangeType.DEMOTE == "demote"


class TestClusterNode:
    def test_required_fields(self) -> None:
        node = ClusterNode(
            node_id="node_1",
            host="192.168.1.1",
            port=8000,
            role=NodeRole.FOLLOWER,
        )
        assert node.node_id == "node_1"
        assert node.host == "192.168.1.1"
        assert node.port == 8000
        assert node.role is NodeRole.FOLLOWER
        assert node.status is NodeStatus.ONLINE
        assert isinstance(node.started_at, datetime)
        assert isinstance(node.last_heartbeat, datetime)
        assert node.metadata == {}

    def test_with_all_fields(self) -> None:
        now = datetime.now()
        node = ClusterNode(
            node_id="node_1",
            host="192.168.1.1",
            port=8000,
            role=NodeRole.LEADER,
            status=NodeStatus.DEGRADED,
            started_at=now,
            last_heartbeat=now,
            metadata={"region": "us-east"},
        )
        assert node.role is NodeRole.LEADER
        assert node.status is NodeStatus.DEGRADED
        assert node.started_at == now
        assert node.metadata == {"region": "us-east"}

    def test_frozen(self) -> None:
        node = ClusterNode(
            node_id="n1",
            host="localhost",
            port=8080,
            role=NodeRole.FOLLOWER,
        )
        with pytest.raises(ValueError):
            node.host = "changed"  # type: ignore[misc]


class TestClusterConfig:
    def test_required_fields(self) -> None:
        config = ClusterConfig(cluster_name="test-cluster")
        assert config.cluster_name == "test-cluster"
        assert config.heartbeat_interval_seconds == 5
        assert config.election_timeout_seconds == 30
        assert config.min_nodes == 1
        assert config.max_nodes == 10

    def test_custom_values(self) -> None:
        config = ClusterConfig(
            cluster_name="prod-cluster",
            heartbeat_interval_seconds=10,
            election_timeout_seconds=60,
            min_nodes=3,
            max_nodes=7,
        )
        assert config.heartbeat_interval_seconds == 10
        assert config.election_timeout_seconds == 60
        assert config.min_nodes == 3
        assert config.max_nodes == 7

    def test_frozen(self) -> None:
        config = ClusterConfig(cluster_name="c")
        with pytest.raises(ValueError):
            config.cluster_name = "changed"  # type: ignore[misc]


class TestClusterState:
    def test_defaults(self) -> None:
        state = ClusterState()
        assert state.leader_id is None
        assert state.nodes == ()
        assert state.term == 0
        assert state.last_applied == 0
        assert state.state == "follower"

    def test_with_fields(self) -> None:
        node = ClusterNode(
            node_id="n1",
            host="h",
            port=1,
            role=NodeRole.FOLLOWER,
        )
        state = ClusterState(
            leader_id="n1",
            nodes=(node,),
            term=3,
            last_applied=42,
            state="leader",
        )
        assert state.leader_id == "n1"
        assert len(state.nodes) == 1
        assert state.term == 3
        assert state.last_applied == 42
        assert state.state == "leader"

    def test_frozen(self) -> None:
        state = ClusterState()
        with pytest.raises(ValueError):
            state.state = "changed"  # type: ignore[misc]


class TestHeartbeat:
    def test_required_fields(self) -> None:
        hb = Heartbeat(node_id="n1")
        assert hb.node_id == "n1"
        assert isinstance(hb.timestamp, datetime)
        assert hb.load == 0.0
        assert hb.status is NodeStatus.ONLINE

    def test_with_fields(self) -> None:
        hb = Heartbeat(
            node_id="n1",
            load=0.75,
            status=NodeStatus.DEGRADED,
        )
        assert hb.load == 0.75
        assert hb.status is NodeStatus.DEGRADED

    def test_frozen(self) -> None:
        hb = Heartbeat(node_id="n1")
        with pytest.raises(ValueError):
            hb.node_id = "changed"  # type: ignore[misc]


class TestMembershipChange:
    def test_required_fields(self) -> None:
        mc = MembershipChange(
            node_id="n1",
            change_type=ChangeType.JOIN,
        )
        assert mc.node_id == "n1"
        assert mc.change_type is ChangeType.JOIN
        assert isinstance(mc.timestamp, datetime)
        assert mc.reason is None

    def test_with_reason(self) -> None:
        mc = MembershipChange(
            node_id="n1",
            change_type=ChangeType.LEAVE,
            reason="maintenance",
        )
        assert mc.reason == "maintenance"

    def test_all_change_types(self) -> None:
        for ct in ChangeType:
            mc = MembershipChange(node_id="n1", change_type=ct)
            assert mc.change_type is ct

    def test_frozen(self) -> None:
        mc = MembershipChange(
            node_id="n1",
            change_type=ChangeType.JOIN,
        )
        with pytest.raises(ValueError):
            mc.node_id = "changed"  # type: ignore[misc]
