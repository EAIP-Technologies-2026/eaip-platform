# `eaip.utilities`

Tiny, dependency-light helpers. Each helper is independently importable so
that callers pay for only what they use.

| Module | Helpers |
| ------ | ------- |
| `async_tools` | `gather_with_concurrency`, `run_with_timeout` |
| `collections` | `chunked`, `first`, `unique` |
| `strings` | `camel_to_snake`, `snake_to_camel`, `truncate` |

The rule: a utility lives here only if it has **no platform state** and
**no business meaning**. Anything else belongs in a dedicated package.
