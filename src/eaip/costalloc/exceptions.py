"""Exception hierarchy for the cost allocation service."""

from __future__ import annotations

from eaip.exceptions import EAIPError, ErrorCode


class CostAllocationError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class RuleNotFoundError(CostAllocationError):
    default_code = ErrorCode.NOT_FOUND
