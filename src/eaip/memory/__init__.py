"""Memory Engine — working, session, long-term, episodic, and semantic memory.

Bundle-017 (EP-0002.8) of the EAIP Platform Foundation Milestone.

Provides:
- Working, Session, Long-Term, Episodic, and Semantic memory types
- Pluggable memory stores (in-memory, vector-backed)
- Memory indexing, retrieval, and search
- Memory lifecycle, expiration, and retention policies
- Memory consolidation and summarization
- Memory relationships and versioning
- Tenant-aware, policy-aware, audit-friendly memory
- Plugin extensibility hooks
- Runtime, Event Bus, Health, Metrics, and Capability integration
"""

from __future__ import annotations

from eaip.memory.base import (
    MemoryHook,
    MemoryIndexer,
    MemoryProvider,
    MemoryRetriever,
    MemoryStore,
    MemorySummarizer,
)
from eaip.memory.consolidation import (
    ConditionalConsolidationStrategy,
    ConsolidationStrategy,
    MemoryConsolidationService,
    NeverConsolidateStrategy,
    TimeBasedConsolidationStrategy,
)
from eaip.memory.engine import MemoryEngine
from eaip.memory.events import (
    MemoryAccessTracked,
    MemoryArchived,
    MemoryConsolidated,
    MemoryCreated,
    MemoryDeleted,
    MemoryEngineEvent,
    MemoryExpired,
    MemoryRetrievalExecuted,
    MemoryRetrieved,
    MemorySearchExecuted,
    MemorySummarized,
    MemoryUpdated,
)
from eaip.memory.exceptions import (
    MemoryConsolidationError,
    MemoryEngineError,
    MemoryError,
    MemoryExpiredError,
    MemoryIndexingError,
    MemoryNotFoundError,
    MemoryRetrievalError,
    MemoryStoreError,
    MemorySummarizationError,
    MemoryValidationError,
)
from eaip.memory.health import MemoryHealthCheck
from eaip.memory.indexing import (
    AlwaysIndexStrategy,
    CompositeIndexer,
    ContentIndexer,
    IndexingStrategy,
    MetadataIndexer,
    NeverIndexStrategy,
    TagIndexer,
)
from eaip.memory.integration import MemoryRuntimeModule
from eaip.memory.lifecycle import (
    CompositeRetentionPolicy,
    MaxAgeRetentionPolicy,
    MaxCountRetentionPolicy,
    MemoryExpirationService,
    MemoryLifecycleManager,
    PriorityRetentionPolicy,
    RetentionPolicy,
)
from eaip.memory.models import (
    ConsolidationConfig,
    ConsolidationReport,
    IndexingConfig,
    MemoryConfig,
    MemoryItem,
    MemoryQuery,
    MemoryRelation,
    MemoryResult,
    MemoryScope,
    MemorySearchResult,
    MemoryStatus,
    MemoryType,
    RetentionConfig,
    ScopedMemoryId,
)
from eaip.memory.registry import MemoryRegistry
from eaip.memory.retrieval import MemoryRetrievalService
from eaip.memory.store import InMemoryStore, MemoryStoreAdapter
from eaip.memory.summarization import ExtractiveMemorySummarizer

__all__ = [
    "AlwaysIndexStrategy",
    "CompositeIndexer",
    "CompositeRetentionPolicy",
    "ConditionalConsolidationStrategy",
    "ConsolidationConfig",
    "ConsolidationReport",
    "ConsolidationStrategy",
    "ContentIndexer",
    "ExtractiveMemorySummarizer",
    "InMemoryStore",
    "IndexingConfig",
    "IndexingStrategy",
    "MaxAgeRetentionPolicy",
    "MaxCountRetentionPolicy",
    "MemoryAccessTracked",
    "MemoryArchived",
    "MemoryConfig",
    "MemoryConsolidated",
    "MemoryConsolidationError",
    "MemoryConsolidationService",
    "MemoryCreated",
    "MemoryDeleted",
    "MemoryEngine",
    "MemoryEngineError",
    "MemoryEngineEvent",
    "MemoryError",
    "MemoryExpirationService",
    "MemoryExpired",
    "MemoryExpiredError",
    "MemoryHealthCheck",
    "MemoryHook",
    "MemoryIndexer",
    "MemoryIndexingError",
    "MemoryItem",
    "MemoryLifecycleManager",
    "MemoryNotFoundError",
    "MemoryProvider",
    "MemoryQuery",
    "MemoryRelation",
    "MemoryResult",
    "MemoryRetrievalError",
    "MemoryRetrievalExecuted",
    "MemoryRetrievalService",
    "MemoryRetrieved",
    "MemoryRetriever",
    "MemoryRuntimeModule",
    "MemoryScope",
    "MemorySearchExecuted",
    "MemorySearchResult",
    "MemoryStatus",
    "MemoryStore",
    "MemoryStoreAdapter",
    "MemoryStoreError",
    "MemorySummarizationError",
    "MemorySummarized",
    "MemorySummarizer",
    "MemoryType",
    "MemoryUpdated",
    "MemoryValidationError",
    "MetadataIndexer",
    "NeverConsolidateStrategy",
    "NeverIndexStrategy",
    "PriorityRetentionPolicy",
    "RetentionConfig",
    "RetentionPolicy",
    "ScopedMemoryId",
    "TagIndexer",
    "TimeBasedConsolidationStrategy",
]
