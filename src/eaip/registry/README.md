# `eaip.registry`

The generic typed registry that powers `capabilities`, `plugins`, and the DI
binding table.

```python
from eaip.registry import Registry

reg = Registry[Greeter](name="greeters", value_type=Greeter)
reg.register("default", DefaultGreeter())
reg.get("default").say_hi()
```

Features:

* **Type safety** — every `register()` checks `isinstance(value, value_type)`.
* **Uniqueness** — duplicate keys raise unless `replace=True`.
* **Observers** — `observe(callback)` receives `RegistryChange` records.
* **Thread safe** — internal `RLock` guards every mutation.
