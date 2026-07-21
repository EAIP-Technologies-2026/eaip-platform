"""Tests for LeaderElection."""

from __future__ import annotations

import pytest

from eaip.cluster.election import LeaderElection
from eaip.cluster.membership import MembershipManager
from eaip.cluster.models import (
    ClusterConfig,
    ClusterNode,
    NodeRole,
)


@pytest.fixture
def config() -> ClusterConfig:
    return ClusterConfig(cluster_name="test-cluster")


@pytest.fixture
def membership(config: ClusterConfig) -> MembershipManager:
    mgr = MembershipManager(config)
    nodes = [
        ClusterNode(
            node_id=f"node_{i}",
            host=f"192.168.1.{i}",
            port=8000,
            role=NodeRole.FOLLOWER,
        )
        for i in range(1, 4)
    ]
    for n in nodes:
        mgr.add_node(n)
    return mgr


class TestLeaderElection:
    def test_initial_state(self, membership: MembershipManager) -> None:
        election = LeaderElection(node_id="node_1", membership=membership)
        assert election.term == 0
        assert election.leader_id is None
        assert election.is_leader is False

    def test_start_election_wins(self, membership: MembershipManager) -> None:
        election = LeaderElection(node_id="node_1", membership=membership)
        result = election.start_election()
        assert result == "node_1"
        assert election.is_leader is True
        assert election.term == 1

    def test_start_election_increments_term(self, membership: MembershipManager) -> None:
        election = LeaderElection(node_id="node_1", membership=membership)
        election.start_election()
        assert election.term == 1
        election.start_election()
        assert election.term == 2

    def test_single_node_majority(self, config: ClusterConfig) -> None:
        mgr = MembershipManager(config)
        mgr.add_node(
            ClusterNode(
                node_id="sole",
                host="localhost",
                port=8000,
                role=NodeRole.FOLLOWER,
            )
        )
        election = LeaderElection(node_id="sole", membership=mgr)
        result = election.start_election()
        assert result == "sole"
        assert election.is_leader is True

    def test_update_leader_newer_term(self, membership: MembershipManager) -> None:
        election = LeaderElection(node_id="node_1", membership=membership)
        election.update_leader("node_2", term=5)
        assert election.leader_id == "node_2"
        assert election.term == 5
        assert election.is_leader is False

    def test_update_leader_older_term(self, membership: MembershipManager) -> None:
        election = LeaderElection(node_id="node_1", membership=membership)
        election.update_leader("node_2", term=5)
        election.update_leader("node_3", term=3)
        assert election.leader_id == "node_2"
        assert election.term == 5

    def test_is_leader_property(self, membership: MembershipManager) -> None:
        election = LeaderElection(node_id="node_1", membership=membership)
        assert election.is_leader is False
        election.update_leader("node_1", term=1)
        assert election.is_leader is True
