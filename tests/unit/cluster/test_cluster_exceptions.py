"""Tests for Cluster exceptions."""

from __future__ import annotations

from eaip.cluster.exceptions import (
    ClusterError,
    ClusterQuorumLostError,
    LeaderNotAvailableError,
    MembershipError,
    NodeNotFoundError,
)
from eaip.exceptions.base import EAIPError, ErrorCode


class TestClusterError:
    def test_base_exception(self) -> None:
        assert issubclass(ClusterError, EAIPError)

    def test_default_code(self) -> None:
        err = ClusterError("generic error")
        assert err.code is ErrorCode.UNKNOWN

    def test_message(self) -> None:
        err = ClusterError("something went wrong")
        assert str(err) == "something went wrong"


class TestNodeNotFoundError:
    def test_code(self) -> None:
        err = NodeNotFoundError("node_42")
        assert err.code is ErrorCode.NOT_FOUND

    def test_message(self) -> None:
        err = NodeNotFoundError("node_42")
        assert "node_42" in str(err)

    def test_node_id_property(self) -> None:
        err = NodeNotFoundError("node_42")
        assert err.node_id == "node_42"


class TestLeaderNotAvailableError:
    def test_code(self) -> None:
        err = LeaderNotAvailableError()
        assert err.code is ErrorCode.PROVIDER_UNAVAILABLE

    def test_default_message(self) -> None:
        err = LeaderNotAvailableError()
        assert "no leader available" in str(err)

    def test_custom_message(self) -> None:
        err = LeaderNotAvailableError("leader is down")
        assert "leader is down" in str(err)


class TestClusterQuorumLostError:
    def test_code(self) -> None:
        err = ClusterQuorumLostError(node_count=2, quorum_required=3)
        assert err.code is ErrorCode.INTERNAL_ERROR

    def test_message(self) -> None:
        err = ClusterQuorumLostError(node_count=2, quorum_required=3)
        assert "2" in str(err)
        assert "3" in str(err)

    def test_properties(self) -> None:
        err = ClusterQuorumLostError(node_count=2, quorum_required=3)
        assert err.node_count == 2
        assert err.quorum_required == 3


class TestMembershipError:
    def test_code(self) -> None:
        err = MembershipError("node already exists")
        assert err.code is ErrorCode.VALIDATION_FAILED

    def test_message(self) -> None:
        err = MembershipError("node already exists")
        assert str(err) == "node already exists"
