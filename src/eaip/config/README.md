# `eaip.config`

Layered configuration loading.

| Source | Purpose |
| ------ | ------- |
| `DictSource` | Literal in-memory dict — used in tests. |
| `EnvSource` | `EAIP_*` environment variables; `__` nests keys. |
| `FileSource` | JSON or TOML file (suffix-detected). |
| `LayeredSource` | Deep-merges multiple sources, later wins. |

`ConfigLoader(source).load(SettingsModel)` parses the resolved mapping into
a typed Pydantic model via `eaip.validation.validate_model`.
