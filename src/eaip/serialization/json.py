"""JSON (de)serialisation with safe defaults for the platform.

The encoder understands:

* :class:`pydantic.BaseModel` (via ``model_dump``)
* :class:`enum.Enum` (via ``value``)
* :class:`datetime.datetime` (ISO-8601, UTC enforced)
* :class:`uuid.UUID`, :class:`pathlib.Path`, :class:`decimal.Decimal`
* dataclasses (via :func:`dataclasses.asdict`)
* arbitrary objects exposing ``to_json()`` or ``__json__``

Any other type raises :class:`SerializationError` rather than silently
producing a string representation.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import decimal
import enum
import json
import pathlib
import uuid
from typing import Any

from pydantic import BaseModel

from eaip.exceptions.domain import SerializationError


class JSONEncoder(json.JSONEncoder):
    """Strict JSON encoder used platform-wide."""

    def default(self, o: Any) -> Any:  # noqa: ANN401 - json.JSONEncoder signature
        if isinstance(o, BaseModel):
            return o.model_dump(mode="json")
        if isinstance(o, enum.Enum):
            return o.value
        if isinstance(o, _dt.datetime):
            if o.tzinfo is None:
                o = o.replace(tzinfo=_dt.UTC)
            return o.isoformat()
        if isinstance(o, _dt.date):
            return o.isoformat()
        if isinstance(o, uuid.UUID):
            return str(o)
        if isinstance(o, pathlib.PurePath):
            return str(o)
        if isinstance(o, decimal.Decimal):
            return str(o)
        if isinstance(o, set | frozenset):
            return sorted(o, key=repr)
        if isinstance(o, bytes | bytearray):
            return o.decode("utf-8")
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)
        for attr in ("__json__", "to_json"):
            method = getattr(o, attr, None)
            if callable(method):
                return method()
        raise SerializationError(
            f"unsupported type for JSON serialisation: {type(o).__name__}",
            context={"type": type(o).__name__},
        )


class JSONDecoder(json.JSONDecoder):
    """Default decoder — provided for symmetry / future extension."""


def to_json(value: Any, *, indent: int | None = None, sort_keys: bool = False) -> str:
    """Serialise ``value`` to a JSON string using the platform encoder."""
    try:
        return json.dumps(
            value,
            cls=JSONEncoder,
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=False,
            separators=(",", ":") if indent is None else (",", ": "),
        )
    except SerializationError:
        raise
    except (TypeError, ValueError) as exc:
        raise SerializationError(str(exc), cause=exc) from exc


def from_json(payload: str | bytes | bytearray) -> Any:
    """Parse a JSON document, raising :class:`SerializationError` on failure."""
    try:
        return json.loads(payload, cls=JSONDecoder)
    except (TypeError, ValueError) as exc:
        raise SerializationError(f"failed to decode JSON: {exc}", cause=exc) from exc


__all__ = ["JSONDecoder", "JSONEncoder", "from_json", "to_json"]
