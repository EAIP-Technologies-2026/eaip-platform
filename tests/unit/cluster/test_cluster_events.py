"""Tests for Cluster domain events."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.cluster.events import (
    ClusterEvent,
    ClusterStateChanged,
    HeartbeatMissed,
    LeaderElected,
    NodeJoined,
    NodeLeft,
    NodePromoted,
)
from eaip.events.event import DomainEvent


class TestNodeJoined:
    def test_defaults(self) -> None:
        event = NodeJoined()
        assert event.event_type == "eaip.cluster.node.joined"
        assert event.node_id == ""
        assert event.host == ""
        assert event.port == 0
        assert event.role == ""
        assert isinstance(event.occurred_at, datetime)

    def test_with_fields(self) -> None:
        event = NodeJoined(
            node_id="n1",
            host="192.168.1.1",
            port=8000,
            role="follower",
        )
        assert event.node_id == "n1"
        assert event.host == "192.168.1.1"
        assert event.port == 8000
        assert event.role == "follower"

    def test_is_domain_event(self) -> None:
        assert issubclass(NodeJoined, DomainEvent)

    def test_frozen(self) -> None:
        event = NodeJoined()
        with pytest.raises(ValueError):
            event.node_id = "changed"  # type: ignore[misc]


class TestNodeLeft:
    def test_defaults(self) -> None:
        event = NodeLeft()
        assert event.event_type == "eaip.cluster.node.left"

    def test_with_fields(self) -> None:
        event = NodeLeft(node_id="n1", reason="shutdown")
        assert event.reason == "shutdown"


class TestNodePromoted:
    def test_defaults(self) -> None:
        event = NodePromoted()
        assert event.event_type == "eaip.cluster.node.promoted"

    def test_with_fields(self) -> None:
        event = NodePromoted(node_id="n1", new_role="leader")
        assert event.new_role == "leader"


class TestLeaderElected:
    def test_defaults(self) -> None:
        event = LeaderElected()
        assert event.event_type == "eaip.cluster.leader.elected"
        assert event.term == 0

    def test_with_fields(self) -> None:
        event = LeaderElected(leader_id="n1", term=3)
        assert event.leader_id == "n1"
        assert event.term == 3


class TestHeartbeatMissed:
    def test_defaults(self) -> None:
        event = HeartbeatMissed()
        assert event.event_type == "eaip.cluster.heartbeat.missed"
        assert event.missed_count == 0

    def test_with_fields(self) -> None:
        event = HeartbeatMissed(node_id="n1", missed_count=5)
        assert event.missed_count == 5


class TestClusterStateChanged:
    def test_defaults(self) -> None:
        event = ClusterStateChanged()
        assert event.event_type == "eaip.cluster.state.changed"

    def test_with_fields(self) -> None:
        event = ClusterStateChanged(
            previous_state="follower",
            new_state="leader",
        )
        assert event.previous_state == "follower"
        assert event.new_state == "leader"


class TestClusterEvent:
    def test_union_type(self) -> None:
        events: list[ClusterEvent] = [
            NodeJoined(),
            NodeLeft(),
            NodePromoted(),
            LeaderElected(),
            HeartbeatMissed(),
            ClusterStateChanged(),
        ]
        assert len(events) == 6
