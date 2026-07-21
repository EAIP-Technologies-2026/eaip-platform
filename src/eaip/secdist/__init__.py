"""Secrets Distribution Service — distribute secrets securely to authorised targets."""

from __future__ import annotations

from eaip.secdist.distributor import SecretDistributor
from eaip.secdist.events import (
    DistributionFailed,
    DistributionRevoked,
    SecretDistributed,
)
from eaip.secdist.exceptions import (
    DistributionFailedError,
    DistributorError,
    TargetNotFoundError,
)
from eaip.secdist.health import SecdistHealthCheck
from eaip.secdist.integration import SecdistRuntimeModule
from eaip.secdist.models import (
    DistributionResult,
    DistributionTarget,
    DistributorConfig,
    SecretPackage,
)

__all__ = [
    "DistributionFailed",
    "DistributionFailedError",
    "DistributionResult",
    "DistributionRevoked",
    "DistributionTarget",
    "DistributorConfig",
    "DistributorError",
    "SecdistHealthCheck",
    "SecdistRuntimeModule",
    "SecretDistributed",
    "SecretDistributor",
    "SecretPackage",
    "TargetNotFoundError",
]
