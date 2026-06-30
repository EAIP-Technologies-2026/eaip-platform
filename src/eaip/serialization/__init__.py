"""Serialisation helpers.

The platform supports JSON natively. Binary formats (msgpack, CBOR) are
implemented by individual capabilities behind the same conceptual API.
"""

from __future__ import annotations

from eaip.serialization.json import (
    JSONDecoder,
    JSONEncoder,
    from_json,
    to_json,
)

__all__ = ["JSONDecoder", "JSONEncoder", "from_json", "to_json"]
