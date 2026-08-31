"""EP-0143 — Cross-Region Replicator — multi-region data replication."""

from __future__ import annotations

from eaip.crossreg.events import (
    ReplicationCompleted,
    ReplicationFailed,
    ReplicationStarted,
)
from eaip.crossreg.exceptions import (
    ReplicationError,
    RuleNotFoundError,
)
from eaip.crossreg.health import CrossRegHealthCheck
from eaip.crossreg.integration import CrossRegRuntimeModule
from eaip.crossreg.models import (
    ReplicationConfig,
    ReplicationRule,
    ReplicationStatus,
)
from eaip.crossreg.replicator import CrossRegionReplicator

__all__ = [
    "CrossRegHealthCheck",
    "CrossRegRuntimeModule",
    "CrossRegionReplicator",
    "ReplicationCompleted",
    "ReplicationConfig",
    "ReplicationError",
    "ReplicationFailed",
    "ReplicationRule",
    "ReplicationStarted",
    "ReplicationStatus",
    "RuleNotFoundError",
]
