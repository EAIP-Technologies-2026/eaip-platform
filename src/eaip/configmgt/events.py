"""Domain events for the configuration management module."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.configmgt.models import ConfigEntry, ConfigProfile, ConfigSnapshot
from eaip.events.event import DomainEvent


class ConfigCreated(DomainEvent):
    event_type: ClassVar[str] = "configmgt.config.created"
    entry: ConfigEntry


class ConfigUpdated(DomainEvent):
    event_type: ClassVar[str] = "configmgt.config.updated"
    entry: ConfigEntry
    old_value: str = ""
    changed_by: str = ""


class ConfigDeleted(DomainEvent):
    event_type: ClassVar[str] = "configmgt.config.deleted"
    entry_id: str
    entry_key: str


class ConfigProfileCreated(DomainEvent):
    event_type: ClassVar[str] = "configmgt.profile.created"
    profile: ConfigProfile


class ConfigProfileApplied(DomainEvent):
    event_type: ClassVar[str] = "configmgt.profile.applied"
    profile_id: str
    profile_name: str
    entries_count: int


class ConfigSnapshotCreated(DomainEvent):
    event_type: ClassVar[str] = "configmgt.snapshot.created"
    snapshot: ConfigSnapshot


class ConfigValidated(DomainEvent):
    event_type: ClassVar[str] = "configmgt.config.validated"
    entry_id: str
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class ConfigValidationFailed(DomainEvent):
    event_type: ClassVar[str] = "configmgt.config.validation_failed"
    entry_id: str
    entry_key: str
    errors: tuple[str, ...] = ()


class ConfigHotReloaded(DomainEvent):
    event_type: ClassVar[str] = "configmgt.config.hot_reloaded"
    changed_keys: tuple[str, ...] = ()
    details: dict[str, Any] = {}


__all__ = [
    "ConfigCreated",
    "ConfigDeleted",
    "ConfigHotReloaded",
    "ConfigProfileApplied",
    "ConfigProfileCreated",
    "ConfigSnapshotCreated",
    "ConfigUpdated",
    "ConfigValidated",
    "ConfigValidationFailed",
]
