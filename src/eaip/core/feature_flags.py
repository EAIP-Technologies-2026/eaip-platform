"""Static feature-flag registry.

The Foundation provides *static* feature flags (enabled/disabled at boot).
Dynamic (runtime-toggle) flags are a separate concern and land in a later
engineering pack.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeatureFlag:
    """Immutable record describing a feature flag."""

    name: str
    default: bool = False
    description: str = ""


class FeatureFlagRegistry:
    """Registers known flags and exposes resolution overlays."""

    def __init__(self) -> None:
        self._flags: dict[str, FeatureFlag] = {}
        self._overrides: dict[str, bool] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def define(self, flag: FeatureFlag) -> None:
        if not flag.name:
            raise ValueError("flag name must be non-empty")
        with self._lock:
            self._flags[flag.name] = flag

    def apply_overrides(
        self, *, enabled: tuple[str, ...] = (), disabled: tuple[str, ...] = ()
    ) -> None:
        """Apply static overrides (typically sourced from settings)."""
        with self._lock:
            for name in enabled:
                self._overrides[name] = True
            for name in disabled:
                self._overrides[name] = False

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------
    def is_enabled(self, name: str) -> bool:
        with self._lock:
            if name in self._overrides:
                return self._overrides[name]
            flag = self._flags.get(name)
            return flag.default if flag else False

    def known(self) -> list[str]:
        with self._lock:
            return sorted(self._flags)


__all__ = ["FeatureFlag", "FeatureFlagRegistry"]
