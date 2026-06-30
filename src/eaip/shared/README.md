# `eaip.shared`

Zero-dependency primitives used by **every** other Foundation layer. This
package must **not** import from any other ``eaip.*`` subpackage.

## Contents

| Module | Purpose |
| ------ | ------- |
| `identifiers` | Typed `str` subclasses (`CorrelationId`, `RunId`, `ComponentId`, `Slug`). |
| `result` | A typed `Result = Ok[T] \| Err[E]` outcome for boundary failures. |
| `sentinels` | `UNSET` marker for distinguishing absence from `None`. |
| `time` | UTC clocks, `Duration`, `TimeProvider`. |
| `types` | JSON value aliases and other primitive type aliases. |

## Design rules

* No I/O, no logging, no globals.
* Public symbols are re-exported from `eaip.shared.__init__`.
* Every public symbol is annotated and typed for `mypy --strict`.
