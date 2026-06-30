# `eaip.capabilities`

Capabilities are **self-describing units of public functionality** the
platform exposes (for example, future EPs will register `agent.run`,
`tool.http`, `memory.vector`). The Foundation only ships the descriptor and
registry — concrete implementations are registered elsewhere (DI container,
plugin loader, factories).

| Symbol | Purpose |
| ------ | ------- |
| `Capability` | Immutable Pydantic record: name, title, version, status, tags. |
| `CapabilityStatus` | `registered` / `enabled` / `disabled` / `deprecated`. |
| `CapabilityRegistry` | Adds enable/disable/deprecate transitions atop a generic `Registry`. |
