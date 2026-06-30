"""Strongly-typed identifier value objects.

All identifiers are frozen ``str`` subclasses; they print like strings, hash
like strings, and are JSON-serialisable, but they are statically distinct
from one another and from plain ``str``. This eliminates an entire class of
"argument confusion" bugs.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Final, Self

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

_SLUG_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")


class _StrId(str):
    """Base class for opaque string identifiers."""

    __slots__ = ()

    @classmethod
    def new(cls) -> Self:
        """Generate a fresh UUIDv4-backed identifier."""
        return cls(str(uuid.uuid4()))

    @classmethod
    def parse(cls, raw: str) -> Self:
        """Parse and validate ``raw`` into an identifier of this type."""
        if not isinstance(raw, str) or not raw:
            raise ValueError(f"{cls.__name__} must be a non-empty string")
        return cls(raw)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: Any, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Tell Pydantic v2 to treat this class as a constrained string."""

        def _validate(value: Any) -> "_StrId":
            if isinstance(value, cls):
                return value
            if isinstance(value, str):
                return cls.parse(value)
            raise TypeError(f"{cls.__name__} expects a string, got {type(value).__name__}")

        return core_schema.no_info_plain_validator_function(
            _validate,
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"{type(self).__name__}({str.__repr__(self)})"


class CorrelationId(_StrId):
    """A request- or run-scoped tracing correlation token."""

    __slots__ = ()


class RunId(_StrId):
    """Identifies a single platform run / execution."""

    __slots__ = ()


class ComponentId(_StrId):
    """Identifies a registered component (service, plugin, capability)."""

    __slots__ = ()


class Slug(str):
    """A DNS-label-compatible lowercase slug (≤ 63 chars)."""

    __slots__ = ()

    def __new__(cls, value: str) -> "Slug":
        if not _SLUG_RE.match(value):
            raise ValueError(
                f"invalid slug {value!r}: must match {_SLUG_RE.pattern}"
            )
        return str.__new__(cls, value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: Any, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        def _validate(value: Any) -> "Slug":
            if isinstance(value, cls):
                return value
            if isinstance(value, str):
                return cls(value)
            raise TypeError(f"Slug expects a string, got {type(value).__name__}")

        return core_schema.no_info_plain_validator_function(
            _validate,
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )


__all__ = ["ComponentId", "CorrelationId", "RunId", "Slug"]
