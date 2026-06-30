# `eaip.adapters`

Namespace package for adapter contracts and (in future engineering packages)
concrete adapter implementations.

The Foundation deliberately ships **no** concrete adapters for external
services (LLMs, vector stores, message buses, ...) — those belong to their
own capability engineering packages.

## Contents shipped in EP-0002

| Subpackage | Purpose |
| ---------- | ------- |
| [`interfaces/`](./interfaces/README.md) | Abstract adapter contracts: `AbstractAdapter`, `AdapterCapability`. |

Future capability packs (EP-0003+) will add subpackages here for LLM, tool,
memory, and policy adapters — each one a subclass of `AbstractAdapter`.
