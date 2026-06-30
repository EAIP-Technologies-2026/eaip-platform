# `eaip.dependency_injection`

A small, explicit DI container.

| Symbol | Purpose |
| ------ | ------- |
| `Container` | The container itself. |
| `Provider` | Internal record describing a binding. |
| `Scope` | `SINGLETON` (default), `TRANSIENT`, `SCOPED`. |

```python
from eaip.dependency_injection import Container, Scope

c = Container()
c.register_instance(Clock, SystemClock())
c.register(Greeter, ConsoleGreeter, scope=Scope.SINGLETON)
greeter = c.resolve(Greeter)
```

Hard guarantees:

* **No magic.** Bindings are declared by hand.
* **Cycle-safe.** Cyclic resolutions raise `DependencyCycleError`.
* **Type-safe.** Bindings whose factories return the wrong type raise `RegistryTypeMismatchError`.
* **Scoped.** `create_scope()` returns a child container sharing singletons with the parent.
