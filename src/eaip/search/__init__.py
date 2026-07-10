"""Enterprise Search & Federation — enterprise-wide search, ranking, pagination,
and provider abstraction.

Bundle-035 of the EAIP Platform Foundation Milestone.

Provides:
- SearchQuery, SearchResult, SearchResultItem, SearchFilter models
- SearchProvider protocol and implementations (KnowledgeSearchProvider,
  MemorySearchProvider, CompositeSearchProvider)
- EnterpriseSearchEngine — federated search across providers with merging,
  deduplication, and pagination
- RankingService — query-aware reranking with configurable weights
- SearchFederation — enterprise/department-scoped federated search
- Domain events, health check, and RuntimeModule integration
"""

from __future__ import annotations

from eaip.search.engine import EnterpriseSearchEngine
from eaip.search.events import (
    ProviderRegistered,
    ProviderSearchExecuted,
    ProviderUnregistered,
    SearchExecuted,
    SearchFederated,
)
from eaip.search.exceptions import (
    ProviderNotFoundError,
    ProviderSearchError,
    SearchError,
    SearchQueryError,
)
from eaip.search.federation import SearchFederation
from eaip.search.health import SearchHealthCheck
from eaip.search.integration import SearchRuntimeModule
from eaip.search.models import (
    Pagination,
    SearchFilter,
    SearchProviderConfig,
    SearchQuery,
    SearchResult,
    SearchResultItem,
)
from eaip.search.providers import (
    CompositeSearchProvider,
    KnowledgeSearchProvider,
    MemorySearchProvider,
    SearchProvider,
)
from eaip.search.ranking import RankingService

__all__ = [
    "CompositeSearchProvider",
    "EnterpriseSearchEngine",
    "KnowledgeSearchProvider",
    "MemorySearchProvider",
    "Pagination",
    "ProviderNotFoundError",
    "ProviderRegistered",
    "ProviderSearchError",
    "ProviderSearchExecuted",
    "ProviderUnregistered",
    "RankingService",
    "SearchError",
    "SearchExecuted",
    "SearchFederated",
    "SearchFederation",
    "SearchFilter",
    "SearchHealthCheck",
    "SearchProvider",
    "SearchProviderConfig",
    "SearchQuery",
    "SearchQueryError",
    "SearchResult",
    "SearchResultItem",
    "SearchRuntimeModule",
]
