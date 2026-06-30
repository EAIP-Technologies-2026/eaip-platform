# `eaip.types`

Constrained value-object types used across configuration and domain models.

These are deliberately **value types** (`Annotated` aliases) rather than
classes so they compose seamlessly with `pydantic.BaseModel` while remaining
zero-cost at runtime.

| Type | Constraint |
| ---- | ---------- |
| `NonEmptyStr` | `str` ≥ 1 char, stripped, ≤ 4096. |
| `Port` | `int` ∈ [1, 65535]. |
| `HostName` | non-empty, no whitespace, ≤ 253 chars. |
| `Url` | requires `scheme://rest`. |
| `LogLevel` | canonicalised to upper-case standard names. |
| `EnvName` | lowercased alphanumeric / `-_`. |
| `Environment` | enum of canonical deployment environments. |
