"""Sentinel values used to distinguish "absent" from ``None``.

``None`` is a legitimate domain value (an explicitly nulled field) in many
APIs, which conflicts with using it as a "no value supplied" marker. The
:data:`UNSET` sentinel makes that distinction explicit and type-safe.
"""

from __future__ import annotations

from enum import Enum
from typing import Final, Literal, Self


class UnsetType(Enum):
    """Singleton enum providing a typed "no value" sentinel.

    Using an ``Enum`` (rather than a bare object) gives static type checkers a
    concrete, narrowable type to reason about.
    """

    UNSET = "UNSET"

    def __bool__(self: Self) -> Literal[False]:  # pragma: no cover - trivial
        """Return False for truthiness check."""
        return False

    def __repr__(self: Self) -> str:  # pragma: no cover - trivial
        """Return the representation of the sentinel."""
        return "UNSET"


#: The canonical sentinel instance.
UNSET: Final[UnsetType] = UnsetType.UNSET

__all__ = ["UNSET", "UnsetType"]
