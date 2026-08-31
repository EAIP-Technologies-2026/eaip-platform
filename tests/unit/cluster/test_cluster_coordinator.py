"""Tests for ClusterCoordinator."""

from __future__ import annotations

import pytest

from eaip.cluster.coordinator import ClusterCoordinator
from eaip.cluster.models import (
    ClusterConfig,
    ClusterNode,
    NodeRole,
)


@pytest.fixture
def config() -> ClusterConfig:
    return ClusterConfig(
        cluster_name="test-cluster",
        heartbeat_interval_seconds=10,
        election_timeout_seconds=30,
    )


@pytest.fixture
def node_a() -> ClusterNode:
    return ClusterNode(
        node_id="node_a",
        host="192.168.1.1",
        port=8000,
        role=NodeRole.FOLLOWER,
    )


class TestClusterCoordinator:
    def test_default_construction(self) -> None:
        coord = ClusterCoordinator()
        assert coord.config.cluster_name == "default"
        assert coord.leader_id is None
        assert coord.is_leader is False

    def test_custom_config(self, config: ClusterConfig) -> None:
        coord = ClusterCoordinator(config=config)
        assert coord.config.cluster_name == "test-cluster"

    def test_properties(self, config: ClusterConfig) -> None:
        coord = ClusterCoordinator(config=config)
        assert coord.config is not None
        assert coord.membership is not None

    async def test_register_node(
        self,
        config: ClusterConfig,
        node_a: ClusterNode,
    ) -> None:
        coord = ClusterCoordinator(config=config)
        await coord.register_node(node_a)
        assert coord.membership.node_count == 1

    async def test_unregister_node(
        self,
        config: ClusterConfig,
        node_a: ClusterNode,
    ) -> None:
        coord = ClusterCoordinator(config=config)
        await coord.register_node(node_a)
        removed = await coord.unregister_node("node_a")
        assert removed == node_a
        assert coord.membership.node_count == 0

    async def test_start_stop(self, config: ClusterConfig) -> None:
        coord = ClusterCoordinator(config=config)
        await coord.start()
        await coord.stop()
