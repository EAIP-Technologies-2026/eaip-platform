"""String helpers used by configuration & serialisation layers."""

from __future__ import annotations

import re
from typing import Final

_CAMEL_BOUNDARY: Final[re.Pattern[str]] = re.compile(r"(?<!^)(?=[A-Z])")


def camel_to_snake(value: str) -> str:
    """Convert ``camelCase``/``PascalCase`` to ``snake_case``."""
    return _CAMEL_BOUNDARY.sub("_", value).lower()


def snake_to_camel(value: str, *, upper_first: bool = False) -> str:
    """Convert ``snake_case`` to ``camelCase`` (or ``PascalCase`` if requested)."""
    parts = value.split("_")
    if not parts:
        return ""
    head, *tail = parts
    head_out = head.capitalize() if upper_first else head
    return head_out + "".join(p.capitalize() for p in tail)


def truncate(value: str, *, max_length: int, ellipsis: str = "…") -> str:
    """Truncate ``value`` to at most ``max_length`` characters (inclusive of ellipsis)."""
    if max_length < len(ellipsis):
        raise ValueError("max_length must be ≥ len(ellipsis)")
    if len(value) <= max_length:
        return value
    return value[: max_length - len(ellipsis)] + ellipsis


__all__ = ["camel_to_snake", "snake_to_camel", "truncate"]
