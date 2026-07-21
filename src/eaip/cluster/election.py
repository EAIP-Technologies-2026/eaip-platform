"""Leader election algorithm for cluster coordination."""

from __future__ import annotations

from eaip.cluster.membership import MembershipManager
from eaip.cluster.models import NodeRole
from eaip.logging.context import get_logger


class LeaderElection:
    """Simple leader election inspired by the Raft consensus algorithm.

    Manages election terms, vote requests, and leader state tracking.
    """

    def __init__(
        self,
        node_id: str,
        membership: MembershipManager,
    ) -> None:
        """Initialize the leader election with a node identity and membership manager."""
        self._node_id = node_id
        self._membership = membership
        self._term = 0
        self._leader_id: str | None = None
        self._voted_for: str | None = None
        self._log = get_logger("eaip.cluster.election")

    @property
    def term(self) -> int:
        """Return the current election term."""
        return self._term

    @property
    def leader_id(self) -> str | None:
        """Return the current leader node id, or None."""
        return self._leader_id

    @property
    def is_leader(self) -> bool:
        """Return True if this node is the current leader."""
        return self._leader_id == self._node_id

    def start_election(self) -> str | None:
        """Start a leader election and return the elected leader id or None."""
        self._term += 1
        self._voted_for = self._node_id
        votes = 1
        for node in self._membership.nodes:
            if (
                node.node_id != self._node_id
                and node.role is NodeRole.FOLLOWER
                and self._request_vote()
            ):
                votes += 1
        majority = (self._membership.node_count // 2) + 1
        if votes >= majority:
            self._leader_id = self._node_id
            return self._node_id
        return None

    def _request_vote(self) -> bool:
        return True

    def update_leader(self, leader_id: str, term: int) -> None:
        """Update the known leader if the term is at least the current term."""
        if term >= self._term:
            self._term = term
            self._leader_id = leader_id


__all__ = ["LeaderElection"]
