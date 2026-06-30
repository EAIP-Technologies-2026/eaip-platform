# `eaip.validation`

Imperative validators that surface a single, typed `ValidationError` so the
rest of the platform never has to reason about which library raised what.

| Helper | Purpose |
| ------ | ------- |
| `ensure(condition, message, **context)` | Assert with structured context. |
| `validate_range(v, minimum=..., maximum=...)` | Inclusive numeric range. |
| `validate_one_of(v, allowed)` | Enum-like membership check. |
| `validate_model(model_cls, data)` | Wraps Pydantic v2 parsing → `ValidationError`. |
