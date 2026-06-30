"""Cross-cutting platform primitives: feature flags & signal handling."""

from __future__ import annotations

from eaip.core.feature_flags import FeatureFlag, FeatureFlagRegistry
from eaip.core.signals import ShutdownSignal, install_shutdown_handlers

__all__ = [
    "FeatureFlag",
    "FeatureFlagRegistry",
    "ShutdownSignal",
    "install_shutdown_handlers",
]
