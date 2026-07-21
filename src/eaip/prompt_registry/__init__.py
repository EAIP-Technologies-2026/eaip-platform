"""Prompt Registry — prompt definition, versioning, lifecycle, and search.

Provides domain models, events, exceptions, and a service layer for managing
prompt definitions and their versions. Supports CRUD, version activation,
rollback, diffing, and search. Integrates with the EAIP runtime via a
:class:`PromptRegistryRuntimeModule` and exposes a health check.
"""

from __future__ import annotations

from eaip.prompt_registry.events import (
    PromptApproved,
    PromptArchived,
    PromptCreated,
    PromptDeleted,
    PromptPublished,
    PromptRegistered,
    PromptRegistryEvent,
    PromptRejected,
    PromptSearched,
    PromptUnregistered,
    PromptUpdated,
    PromptVersionActivated,
    PromptVersionArchived,
    PromptVersionCompared,
    PromptVersionCreated,
    PromptVersionDeactivated,
    PromptVersionRolledBack,
)
from eaip.prompt_registry.exceptions import (
    PromptApprovalError,
    PromptArchivalError,
    PromptNotFoundError,
    PromptPublishError,
    PromptRegistryError,
    PromptTemplateError,
    PromptValidationError,
    PromptVersionConflictError,
    PromptVersionNotFoundError,
)
from eaip.prompt_registry.health import PromptRegistryHealthCheck
from eaip.prompt_registry.integration import PromptRegistryRuntimeModule
from eaip.prompt_registry.models import (
    PromptApprovalStatus,
    PromptCategory,
    PromptDefinition,
    PromptDiffResult,
    PromptMetadata,
    PromptParameter,
    PromptRegistryConfig,
    PromptSearchResult,
    PromptStatus,
    PromptTag,
    PromptTemplate,
    PromptVariable,
    PromptVersion,
    PromptVersionStatus,
)
from eaip.prompt_registry.service import PromptRegistryService

__all__ = [
    "PromptApprovalError",
    "PromptApprovalStatus",
    "PromptApproved",
    "PromptArchivalError",
    "PromptArchived",
    "PromptCategory",
    "PromptCreated",
    "PromptDefinition",
    "PromptDeleted",
    "PromptDiffResult",
    "PromptMetadata",
    "PromptNotFoundError",
    "PromptParameter",
    "PromptPublishError",
    "PromptPublished",
    "PromptRegistered",
    "PromptRegistryConfig",
    "PromptRegistryError",
    "PromptRegistryEvent",
    "PromptRegistryHealthCheck",
    "PromptRegistryRuntimeModule",
    "PromptRegistryService",
    "PromptRejected",
    "PromptSearchResult",
    "PromptSearched",
    "PromptStatus",
    "PromptTag",
    "PromptTemplate",
    "PromptTemplateError",
    "PromptUnregistered",
    "PromptUpdated",
    "PromptValidationError",
    "PromptVariable",
    "PromptVersion",
    "PromptVersionActivated",
    "PromptVersionArchived",
    "PromptVersionCompared",
    "PromptVersionConflictError",
    "PromptVersionCreated",
    "PromptVersionDeactivated",
    "PromptVersionNotFoundError",
    "PromptVersionRolledBack",
    "PromptVersionStatus",
]
