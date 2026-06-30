# `eaip.interfaces`

Abstract base classes that enforce stricter contracts than the structural
protocols in [`eaip.protocols`](../protocols/README.md).

| Interface | Purpose |
| --------- | ------- |
| `AbstractService` | Managed lifecycle FSM (created → running → stopped). Subclasses implement `_on_start` / `_on_stop`. |
| `AbstractRepository[ID, T]` | Async CRUD contract for storage adapters. |

Use **interfaces** when default behaviour or a `isinstance` taxonomy is
desirable; otherwise prefer **protocols** for looser coupling.
