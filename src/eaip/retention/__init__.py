"""Data Retention & Purge Service — manage policies and execute purge jobs."""

from __future__ import annotations

from eaip.retention.events import (
    PolicyCreated,
    PolicyDeleted,
    PolicyUpdated,
    PurgeExecuted,
)
from eaip.retention.exceptions import (
    PolicyNotFoundError,
    PurgeExecutionError,
    RetentionError,
)
from eaip.retention.health import RetentionHealthCheck
from eaip.retention.integration import RetentionRuntimeModule
from eaip.retention.models import (
    PolicyScope,
    PurgeJob,
    PurgeStatus,
    RetentionConfig,
    RetentionPolicy,
)
from eaip.retention.service import RetentionService

__all__ = [
    "PolicyCreated",
    "PolicyDeleted",
    "PolicyNotFoundError",
    "PolicyScope",
    "PolicyUpdated",
    "PurgeExecuted",
    "PurgeExecutionError",
    "PurgeJob",
    "PurgeStatus",
    "RetentionConfig",
    "RetentionError",
    "RetentionHealthCheck",
    "RetentionPolicy",
    "RetentionRuntimeModule",
    "RetentionService",
]
