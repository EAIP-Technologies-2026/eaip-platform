# `eaip.memory`

Enterprise Memory Engine — working, session, long-term, episodic, and semantic memory.

Bundle-017 (EP-0002.8) of the EAIP Platform Foundation Milestone.

```python
from eaip.memory import MemoryEngine, InMemoryStore

engine = MemoryEngine(InMemoryStore())
item = await engine.create_memory("hello", MemoryType.WORKING, scope)
```

## Modules

| Module | Purpose |
| ------ | ------- |
| `models.py` | MemoryItem, MemoryScope, MemoryQuery, MemoryConfig, and configuration models |
| `base.py` | Protocols: MemoryStore, MemoryIndexer, MemoryRetriever, MemoryProvider |
| `store.py` | InMemoryStore (dict-backed), MemoryStoreAdapter (store + indexer + retriever) |
| `registry.py` | MemoryRegistry — in-memory catalog with relationship tracking |
| `retrieval.py` | MemoryRetrievalService — by ID, type, tags, relations, and free-form search |
| `engine.py` | MemoryEngine — high-level API orchestrating all subsystems |
| `indexing.py` | ContentIndexer, TagIndexer, MetadataIndexer, CompositeIndexer |
| `consolidation.py` | TimeBased, Never, Conditional strategies + MemoryConsolidationService |
| `lifecycle.py` | MaxAge, MaxCount, Priority retention policies + MemoryExpirationService |
| `summarization.py` | ExtractiveMemorySummarizer — deterministic snippet extraction |
| `events.py` | 13 domain event types (MemoryCreated, MemoryUpdated, etc.) |
| `exceptions.py` | 10 exception classes under MemoryError |
| `health.py` | MemoryHealthCheck — HealthReport for platform health rollup |
| `integration.py` | MemoryIntegration / MemoryRuntimeModule — kernel lifecycle wiring |

## Memory types

- **Working** — ephemeral task context (TTL: 1h, max: 50)
- **Session** — conversation/interaction memory (TTL: 24h, max: 200)
- **Long-Term** — persistent across sessions (TTL: 30d)
- **Episodic** — specific events and experiences (TTL: 7d)
- **Semantic** — factual knowledge, never expires by default

## Key contracts

* All timestamps are UTC, timezone-aware.
* MemoryItems are frozen Pydantic models (immutable after creation).
* Scopes provide tenant isolation: `tenant_id:user_id:session_id:application_id`.
* Domain events are published through an optional `event_publisher` callable.
* Authorization is pluggable via an `authorize_fn(action, scope)` callback.
