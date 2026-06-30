"""Deployment-environment enumeration."""

from __future__ import annotations

from enum import StrEnum
from typing import Self


class Environment(StrEnum):
    """Standard deployment environments.

    The platform makes no assumptions about *how many* environments exist in
    a given deployment — only that each environment has a well-known name so
    that policies and defaults can branch on it.
    """

    LOCAL = "local"
    TEST = "test"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

    @classmethod
    def parse(cls, raw: str) -> Self:
        """Parse common aliases (e.g. ``dev`` → ``development``)."""
        normalised = raw.strip().lower()
        aliases = {
            "dev": cls.DEVELOPMENT,
            "stage": cls.STAGING,
            "prod": cls.PRODUCTION,
            "qa": cls.TEST,
        }
        if normalised in aliases:
            return aliases[normalised]  # type: ignore[return-value]
        try:
            return cls(normalised)
        except ValueError as exc:
            raise ValueError(
                f"unknown environment {raw!r}; expected one of "
                f"{', '.join(e.value for e in cls)}"
            ) from exc

    @property
    def is_production_like(self) -> bool:
        """Whether this environment should be treated with production caution."""
        return self in {Environment.STAGING, Environment.PRODUCTION}


__all__ = ["Environment"]
