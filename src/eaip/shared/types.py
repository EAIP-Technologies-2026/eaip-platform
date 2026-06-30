"""Primitive type aliases shared platform-wide.

These aliases are intentionally narrow so that public APIs can advertise
exactly the shape of data they accept or return.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeAlias

#: A value that survives a JSON round-trip without loss.
JSONValue: TypeAlias = (
    "None | bool | int | float | str | JSONArray | JSONObject"
)
#: An ordered collection of JSON values.
JSONArray: TypeAlias = Sequence["JSONValue"]
#: A string-keyed mapping of JSON values.
JSONObject: TypeAlias = Mapping[str, "JSONValue"]

#: A non-secret, opaque string token (e.g. correlation IDs).
OpaqueToken: TypeAlias = str

#: Bytes intended to remain opaque to the platform (e.g. encoded payloads).
Bytes: TypeAlias = bytes

__all__ = [
    "Bytes",
    "JSONArray",
    "JSONObject",
    "JSONValue",
    "OpaqueToken",
]
