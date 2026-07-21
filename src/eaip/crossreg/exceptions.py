"""Exception hierarchy for the cross-region replicator."""

from __future__ import annotations

from eaip.exceptions import EAIPError, ErrorCode


class ReplicationError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class RuleNotFoundError(ReplicationError):
    default_code = ErrorCode.NOT_FOUND
