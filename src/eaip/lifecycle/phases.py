"""Lifecycle phases the manager transitions through."""

from __future__ import annotations

from enum import StrEnum


class LifecyclePhase(StrEnum):
    """Discrete phases of the platform lifecycle."""

    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


__all__ = ["LifecyclePhase"]
