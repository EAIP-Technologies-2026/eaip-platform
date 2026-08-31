# `eaip.lifecycle`

Application lifecycle orchestration.

```python
from eaip.lifecycle import LifecycleManager

lm = LifecycleManager()
lm.add("db", start=db.connect, stop=db.disconnect)
lm.add("server", start=server.serve, stop=server.shutdown)
await lm.start()  # in registration order
...
await lm.stop()  # in reverse order
```

Guarantees:

* **Phase machine** — `CREATED → STARTING → RUNNING → STOPPING → STOPPED`, with `FAILED` from any start failure.
* **Rollback on failure** — partial startups stop already-started hooks LIFO.
* **Mixed sync/async hooks** — both are accepted; the manager normalises them.
* **Idempotent stop** — calling `stop()` when already STOPPED is a no-op.
