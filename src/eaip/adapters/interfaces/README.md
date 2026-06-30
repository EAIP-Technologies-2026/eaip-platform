# `eaip.adapters.interfaces`

Abstract adapter contracts. The Foundation defines only the *shape*; concrete
adapters for LLMs, vector stores, message buses, etc. land in their own
engineering packages.

`AbstractAdapter` requires three things from every implementer:

1. `metadata` — a `ComponentMetadata` describing identity & version.
2. `capabilities` — a tuple of `AdapterCapability` labels.
3. `async health() -> bool` — lightweight self-check.
