# `eaip.exceptions`

A single, consistent exception hierarchy used by every Foundation layer.

## Layout

```text
EAIPError                     (base, carries ErrorCode + context + severity)
├── ConfigurationError
├── ValidationError
├── NotFoundError
├── DependencyError
│   └── DependencyCycleError
├── LifecycleError
├── RegistryError
│   ├── DuplicateRegistrationError
│   └── RegistryTypeMismatchError
├── PluginError
│   └── PluginContractViolationError
└── SerializationError
```

## Guarantees

- Every exception has a stable `ErrorCode` (`EAIP-XXXX`).
- Errors carry structured `context` for observability.
- `with_context(**extra)` is non-mutating; chains preserve `__cause__`.
- `to_dict()` produces JSON-safe payloads suitable for structured logs.
