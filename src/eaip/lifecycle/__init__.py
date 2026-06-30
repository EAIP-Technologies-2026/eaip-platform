"""Application lifecycle manager — ordered startup & reverse-ordered shutdown."""

from __future__ import annotations

from eaip.lifecycle.manager import LifecycleManager
from eaip.lifecycle.phases import LifecyclePhase

__all__ = ["LifecycleManager", "LifecyclePhase"]
