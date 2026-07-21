"""Git Integration Service — repository management, webhook handling, commit indexing."""

from __future__ import annotations

from eaip.gitsvc.events import (
    BranchUpdated,
    CommitIndexed,
    RepositoryRegistered,
    WebhookReceived,
)
from eaip.gitsvc.exceptions import (
    GitServiceError,
    RepositoryNotFoundError,
)
from eaip.gitsvc.health import GitServiceHealthCheck
from eaip.gitsvc.integration import GitServiceRuntimeModule
from eaip.gitsvc.models import GitCommit, GitConfig, GitRepository, GitWebhookEvent
from eaip.gitsvc.service import GitIntegrationService

__all__ = [
    "BranchUpdated",
    "CommitIndexed",
    "GitCommit",
    "GitConfig",
    "GitIntegrationService",
    "GitRepository",
    "GitServiceError",
    "GitServiceHealthCheck",
    "GitServiceRuntimeModule",
    "GitWebhookEvent",
    "RepositoryNotFoundError",
    "RepositoryRegistered",
    "WebhookReceived",
]
