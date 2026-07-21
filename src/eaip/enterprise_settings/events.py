"""Domain events for the enterprise settings module."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.enterprise_settings.models import (
    EnterpriseSettings,
    SettingsAuditEntry,
    SettingsCategory,
    SettingsGroup,
    SettingsProfile,
    SettingsTemplate,
    SettingsValidation,
)
from eaip.events.event import DomainEvent


class EnterpriseSettingsCreated(DomainEvent):
    """Emitted when an enterprise setting is created."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.created"
    setting: EnterpriseSettings


class EnterpriseSettingsUpdated(DomainEvent):
    """Emitted when an enterprise setting is updated."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.updated"
    setting: EnterpriseSettings
    old_value: Any = None
    changed_by: str = ""


class EnterpriseSettingsDeleted(DomainEvent):
    """Emitted when an enterprise setting is deleted."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.deleted"
    setting_id: str
    setting_key: str


class EnterpriseSettingsCategoryCreated(DomainEvent):
    """Emitted when a settings category is created."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.category.created"
    category: SettingsCategory


class EnterpriseSettingsCategoryUpdated(DomainEvent):
    """Emitted when a settings category is updated."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.category.updated"
    category: SettingsCategory


class EnterpriseSettingsCategoryDeleted(DomainEvent):
    """Emitted when a settings category is deleted."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.category.deleted"
    category: SettingsCategory


class EnterpriseSettingsGroupCreated(DomainEvent):
    """Emitted when a settings group is created."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.group.created"
    group: SettingsGroup


class EnterpriseSettingsGroupUpdated(DomainEvent):
    """Emitted when a settings group is updated."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.group.updated"
    group: SettingsGroup


class EnterpriseSettingsGroupDeleted(DomainEvent):
    """Emitted when a settings group is deleted."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.group.deleted"
    group_id: str
    group_name: str


class EnterpriseSettingsProfileActivated(DomainEvent):
    """Emitted when a settings profile is activated."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.profile.activated"
    profile: SettingsProfile


class EnterpriseSettingsProfileDeactivated(DomainEvent):
    """Emitted when a settings profile is deactivated."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.profile.deactivated"
    profile_id: str
    profile_name: str


class EnterpriseSettingsExported(DomainEvent):
    """Emitted when enterprise settings are exported."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.exported"
    export_format: str
    categories: tuple[SettingsCategory, ...] = ()
    exported_by: str = ""


class EnterpriseSettingsImported(DomainEvent):
    """Emitted when enterprise settings are imported."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.imported"
    import_format: str
    import_mode: str = "merge"
    imported_by: str = ""


class EnterpriseSettingsValidated(DomainEvent):
    """Emitted when an enterprise setting is validated."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.validated"
    validation: SettingsValidation


class EnterpriseSettingsAuditLogged(DomainEvent):
    """Emitted when a settings audit entry is logged."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.audit_logged"
    audit_entry: SettingsAuditEntry


class EnterpriseSettingsHistoryRecorded(DomainEvent):
    """Emitted when a settings history entry is recorded."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.history_recorded"
    setting_id: str
    setting_key: str = ""
    old_value: Any = None
    new_value: Any = None
    changed_by: str = ""


class EnterpriseSettingsTemplateApplied(DomainEvent):
    """Emitted when a settings template is applied."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.template_applied"
    template: SettingsTemplate
    applied_by: str = ""


class EnterpriseSettingsEnvironmentOverrideSet(DomainEvent):
    """Emitted when an environment override is set."""

    event_type: ClassVar[str] = "eaip.enterprise_settings.environment_override_set"
    setting_key: str
    environment: str
    value: Any = None
    set_by: str = ""


__all__ = [
    "EnterpriseSettingsAuditLogged",
    "EnterpriseSettingsCategoryCreated",
    "EnterpriseSettingsCategoryDeleted",
    "EnterpriseSettingsCategoryUpdated",
    "EnterpriseSettingsCreated",
    "EnterpriseSettingsDeleted",
    "EnterpriseSettingsEnvironmentOverrideSet",
    "EnterpriseSettingsExported",
    "EnterpriseSettingsGroupCreated",
    "EnterpriseSettingsGroupDeleted",
    "EnterpriseSettingsGroupUpdated",
    "EnterpriseSettingsHistoryRecorded",
    "EnterpriseSettingsImported",
    "EnterpriseSettingsProfileActivated",
    "EnterpriseSettingsProfileDeactivated",
    "EnterpriseSettingsTemplateApplied",
    "EnterpriseSettingsUpdated",
    "EnterpriseSettingsValidated",
]
