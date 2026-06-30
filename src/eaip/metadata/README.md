# `eaip.metadata`

Self-describing metadata attached to every component (service, adapter,
plugin, capability). Registries surface this metadata so operators can
introspect what's loaded without reading source.

| Class | Purpose |
| ----- | ------- |
| `ComponentKind` | Coarse taxonomy (service / adapter / plugin / capability / infrastructure / utility). |
| `ComponentMetadata` | Immutable Pydantic record with name, kind, version, description, vendor, stability, tags. |
