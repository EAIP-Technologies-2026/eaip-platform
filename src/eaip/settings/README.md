# `eaip.settings`

The platform's **canonical settings hierarchy**, built on
[`pydantic-settings`](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).

```
PlatformSettings
├── core: CoreSettings              # app_name, environment, instance_id, debug
├── logging: LoggingSettings        # level, format, include_caller
└── feature_flags: FeatureFlagSettings
```

All variables are loaded from `EAIP_*` env vars with `__` as the nesting
delimiter. `extra="forbid"` ensures typos fail fast.

For arbitrary config sources (files, dicts, layered), use `eaip.config`.
