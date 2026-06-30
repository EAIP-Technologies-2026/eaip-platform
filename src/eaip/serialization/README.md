# `eaip.serialization`

JSON (de)serialisation with **strict, predictable defaults**.

The encoder accepts Pydantic models, enums, dataclasses, UUIDs, paths, dates,
decimals, sets, bytes (UTF-8), and any object exposing `__json__` / `to_json()`.
Anything else raises `SerializationError` — silent string-coercion is a
common source of production bugs we refuse to inherit.

Capabilities requiring other formats (msgpack, CBOR, protobuf) implement
them in their own packages but follow the same naming pattern.
