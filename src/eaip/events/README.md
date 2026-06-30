# `eaip.events`

In-process pub/sub bus for **domain events** (not log records, not metrics).

| Symbol | Purpose |
| ------ | ------- |
| `DomainEvent` | Frozen Pydantic base — subclasses declare `event_type` & payload. |
| `EventBus` | Type-routed bus supporting sync & async subscribers. |
| `Subscription` | Opaque handle returned by `subscribe()` for later `unsubscribe()`. |

## Safety invariants

* Subscriber failures are isolated — one bad handler cannot break others.
* Failures are returned as `(subscription, exception)` tuples for inspection.
* Subscriptions support polymorphic matching (`include_subclasses=True` by default).

Cross-process delivery is out of scope here — it lands in a later capability.
