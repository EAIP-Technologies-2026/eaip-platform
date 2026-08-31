"""Exception hierarchy for firewall rule management."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class FirewallError(EAIPError):
    """Base exception for firewall rule errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class RuleNotFoundError(FirewallError):
    """Raised when a firewall rule is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "FirewallError",
    "RuleNotFoundError",
]
