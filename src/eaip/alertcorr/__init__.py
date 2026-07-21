"""Alert Correlation & Noise Reduction — group related alerts, deduplicate, and suppress noise."""

from __future__ import annotations

from eaip.alertcorr.correlator import AlertCorrelator
from eaip.alertcorr.events import (
    AlertDeduplicated,
    AlertGrouped,
    AlertSuppressed,
)
from eaip.alertcorr.exceptions import (
    CorrelationError,
    RuleNotFoundError,
)
from eaip.alertcorr.health import AlertCorrelationHealthCheck
from eaip.alertcorr.integration import AlertCorrelationRuntimeModule
from eaip.alertcorr.models import (
    Alert,
    AlertGroup,
    CorrelationConfig,
    CorrelationRule,
)

__all__ = [
    "Alert",
    "AlertCorrelationHealthCheck",
    "AlertCorrelationRuntimeModule",
    "AlertCorrelator",
    "AlertDeduplicated",
    "AlertGroup",
    "AlertGrouped",
    "AlertSuppressed",
    "CorrelationConfig",
    "CorrelationError",
    "CorrelationRule",
    "RuleNotFoundError",
]
