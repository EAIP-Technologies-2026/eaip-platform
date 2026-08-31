"""Event Retention Manager — EP-0160."""

from __future__ import annotations

from eaip.eventret.events import (
    PolicyApplied,
    PolicyCreated,
    RetentionJobCompleted,
    RetentionJobFailed,
)
from eaip.eventret.exceptions import (
    EventRetentionError,
    PolicyNotFoundError,
)
from eaip.eventret.health import EventRetentionHealthCheck
from eaip.eventret.integration import EventRetentionRuntimeModule
from eaip.eventret.manager import EventRetentionManager
from eaip.eventret.models import (
    EventRetentionConfig,
    RetentionAction,
    RetentionJob,
    RetentionJobStatus,
    RetentionPolicy,
)

__all__ = [
    "EventRetentionConfig",
    "EventRetentionError",
    "EventRetentionHealthCheck",
    "EventRetentionManager",
    "EventRetentionRuntimeModule",
    "PolicyApplied",
    "PolicyCreated",
    "PolicyNotFoundError",
    "RetentionAction",
    "RetentionJob",
    "RetentionJobCompleted",
    "RetentionJobFailed",
    "RetentionJobStatus",
    "RetentionPolicy",
]
