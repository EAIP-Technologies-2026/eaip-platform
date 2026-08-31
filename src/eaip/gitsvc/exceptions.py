"""Exception hierarchy for Git integration."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class GitServiceError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class RepositoryNotFoundError(GitServiceError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "GitServiceError",
    "RepositoryNotFoundError",
]
