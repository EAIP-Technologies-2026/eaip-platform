"""Feature Flag & Experimentation Engine — flags, rollout, A/B testing, telemetry."""

from __future__ import annotations

from eaip.features.events import (
    ExperimentCompleted,
    ExperimentCreated,
    ExperimentResultRecorded,
    ExperimentStarted,
    FlagCreated,
    FlagDisabled,
    FlagEnabled,
    FlagRolloutChanged,
    FlagUpdated,
    VariantAssigned,
)
from eaip.features.exceptions import (
    ExperimentCompleteError,
    ExperimentNotFoundError,
    FeatureError,
    FlagNotEnabledError,
    FlagNotFoundError,
    InvalidRolloutError,
)
from eaip.features.experiments import ExperimentService
from eaip.features.health import FeatureHealthCheck
from eaip.features.integration import FeatureRuntimeModule
from eaip.features.manager import FeatureManager
from eaip.features.models import (
    Experiment,
    ExperimentResult,
    ExperimentStatus,
    ExperimentVariant,
    FeatureConfig,
    FeatureFlag,
    Operator,
    TargetingRule,
)
from eaip.features.rollout import RolloutManager

__all__ = [
    "Experiment",
    "ExperimentCompleteError",
    "ExperimentCompleted",
    "ExperimentCreated",
    "ExperimentNotFoundError",
    "ExperimentResult",
    "ExperimentResultRecorded",
    "ExperimentService",
    "ExperimentStarted",
    "ExperimentStatus",
    "ExperimentVariant",
    "FeatureConfig",
    "FeatureError",
    "FeatureFlag",
    "FeatureHealthCheck",
    "FeatureManager",
    "FeatureRuntimeModule",
    "FlagCreated",
    "FlagDisabled",
    "FlagEnabled",
    "FlagNotEnabledError",
    "FlagNotFoundError",
    "FlagRolloutChanged",
    "FlagUpdated",
    "InvalidRolloutError",
    "Operator",
    "RolloutManager",
    "TargetingRule",
    "VariantAssigned",
]
