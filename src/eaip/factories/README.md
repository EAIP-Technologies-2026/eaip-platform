# `eaip.factories`

Generic, typed factory keyed by string identifier.

```python
from eaip.factories import Factory

builders = Factory[str](name="greeters")
builders.register("hello", lambda name: f"hello {name}")
builders.create("hello", name="world")  # "hello world"
```

Failures use the platform exception hierarchy:

* `DuplicateRegistrationError` — registering an existing key without `replace=True`.
* `NotFoundError` — calling `create` with an unknown key.
