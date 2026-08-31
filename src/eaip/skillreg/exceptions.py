"""Exception hierarchy for the agent skill registry."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class SkillRegistryError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class SkillNotFoundError(SkillRegistryError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "SkillNotFoundError",
    "SkillRegistryError",
]
