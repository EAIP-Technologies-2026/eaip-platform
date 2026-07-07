"""Redaction processor for sensitive log keys."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, cast

import structlog

_REDACTED: str = "***REDACTED***"


def redact_processor(keys: Iterable[str]) -> structlog.types.Processor:
    """Build a ``structlog`` processor that redacts values for ``keys``.

    Matching is case-insensitive. Redaction recurses into nested mappings.

    Args:
        keys: The keys to redact.

    Returns:
        A ``structlog`` processor.
    """
    lowered = {k.lower() for k in keys}

    def _redact(value: Any) -> Any:
        """Recursively redact values."""
        if isinstance(value, Mapping):
            return {
                k: (_REDACTED if str(k).lower() in lowered else _redact(v))
                for k, v in value.items()
            }
        if isinstance(value, list | tuple):
            redacted = [_redact(v) for v in value]
            return type(value)(redacted) if isinstance(value, tuple) else redacted
        return value

    def processor(
        _logger: object, _method: str, event_dict: structlog.types.EventDict
    ) -> structlog.types.EventDict:
        """The processor function."""
        return cast(structlog.types.EventDict, _redact(event_dict))

    return processor


__all__ = ["redact_processor"]
