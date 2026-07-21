"""Exception hierarchy for the IP reputation service."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ReputationError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class IPNotFoundError(ReputationError):
    default_code = ErrorCode.NOT_FOUND

    def __init__(self, ip: str) -> None:
        self.ip = ip
        super().__init__(f"IP not found: {ip!r}")


__all__ = [
    "IPNotFoundError",
    "ReputationError",
]
