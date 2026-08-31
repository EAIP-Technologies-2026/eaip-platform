"""Domain events raised by the admin package."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class AdminActionExecuted(DomainEvent):
    """Published after an administrative action is executed."""

    event_type: ClassVar[str] = "eaip.admin.action_executed"

    action_id: str
    action_type: str
    target: str
    performed_by: str
    result: str
    details: dict[str, Any] = Field(default_factory=dict)


class AuditEntryCreated(DomainEvent):
    """Published after a new audit entry is recorded."""

    event_type: ClassVar[str] = "eaip.admin.audit_entry_created"

    entry_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    outcome: str


class ConfigChanged(DomainEvent):
    """Published when a configuration value is changed."""

    event_type: ClassVar[str] = "eaip.admin.config_changed"

    key: str
    old_value: Any = None
    new_value: Any = None
    changed_by: str = "system"
    timestamp: datetime | None = None


class CapabilityToggled(DomainEvent):
    """Published when a capability is enabled or disabled."""

    event_type: ClassVar[str] = "eaip.admin.capability_toggled"

    name: str
    enabled: bool
    toggled_by: str = "system"


class PluginReloaded(DomainEvent):
    """Published after a plugin is reloaded."""

    event_type: ClassVar[str] = "eaip.admin.plugin_reloaded"

    plugin_name: str
    success: bool
    message: str = ""
