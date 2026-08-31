"""Enterprise Brain — centralized intelligence layer.

Bundle-031: Orchestrates knowledge, memory, context, and agent
insights across the entire enterprise.

Bundle-032: Department Brains — scoped brain instances for individual
business departments with access control and specialized configuration.

Provides:
- EnterpriseBrain — query orchestration across all sources
- DepartmentBrain — scoped query orchestration for departments
- BrainRegistry — registry for enterprise and department brains
- BrainAccessManager — subject/role-based access control
- BrainQuery, BrainResult, BrainSource, EnterpriseBrainConfig models
- Domain events for observability
- Health checks and runtime module integration
"""

from __future__ import annotations

from eaip.brain.access import BrainAccessManager, BrainSubject
from eaip.brain.brain_registry import BrainRegistry
from eaip.brain.department_brain import DepartmentBrain, DepartmentBrainConfig
from eaip.brain.enterprise_brain import EnterpriseBrain
from eaip.brain.events import (
    BrainAccessDenied,
    BrainContextBuilt,
    BrainEvent,
    BrainKnowledgeRetrieved,
    BrainMemoryRetrieved,
    BrainQueryExecuted,
    BrainSyncCompleted,
    DepartmentBrainQueryExecuted,
)
from eaip.brain.exceptions import (
    BrainAccessDeniedError,
    BrainError,
    BrainQueryError,
    BrainSourceUnavailableError,
)
from eaip.brain.health import BrainHealthCheck
from eaip.brain.integration import BrainRuntimeModule, create_brain_integration
from eaip.brain.models import (
    BrainQuery,
    BrainResult,
    BrainSource,
    EnterpriseBrainConfig,
)

__all__ = [
    "BrainAccessDenied",
    "BrainAccessDeniedError",
    "BrainAccessManager",
    "BrainContextBuilt",
    "BrainError",
    "BrainEvent",
    "BrainHealthCheck",
    "BrainKnowledgeRetrieved",
    "BrainMemoryRetrieved",
    "BrainQuery",
    "BrainQueryError",
    "BrainQueryExecuted",
    "BrainRegistry",
    "BrainResult",
    "BrainRuntimeModule",
    "BrainSource",
    "BrainSourceUnavailableError",
    "BrainSubject",
    "BrainSyncCompleted",
    "DepartmentBrain",
    "DepartmentBrainConfig",
    "DepartmentBrainQueryExecuted",
    "EnterpriseBrain",
    "EnterpriseBrainConfig",
    "create_brain_integration",
]
