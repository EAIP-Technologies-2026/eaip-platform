"""Enterprise settings service — CRUD for settings, categories, groups, profiles, and more."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from eaip.enterprise_settings.events import (
    EnterpriseSettingsCategoryCreated,
    EnterpriseSettingsCategoryDeleted,
    EnterpriseSettingsCreated,
    EnterpriseSettingsDeleted,
    EnterpriseSettingsEnvironmentOverrideSet,
    EnterpriseSettingsExported,
    EnterpriseSettingsGroupCreated,
    EnterpriseSettingsGroupDeleted,
    EnterpriseSettingsHistoryRecorded,
    EnterpriseSettingsImported,
    EnterpriseSettingsProfileActivated,
    EnterpriseSettingsProfileDeactivated,
    EnterpriseSettingsTemplateApplied,
    EnterpriseSettingsUpdated,
    EnterpriseSettingsValidated,
)
from eaip.enterprise_settings.exceptions import (
    EnterpriseSettingsCategoryError,
    EnterpriseSettingsNotFoundError,
    EnterpriseSettingsProfileError,
    EnterpriseSettingsValidationError,
)
from eaip.enterprise_settings.models import (
    EnterpriseSettings,
    SettingsAuditEntry,
    SettingsCategory,
    SettingsConfig,
    SettingsDefinition,
    SettingsEnvironmentOverride,
    SettingsExport,
    SettingsGroup,
    SettingsHistoryEntry,
    SettingsImport,
    SettingsNotification,
    SettingsPermission,
    SettingsProfile,
    SettingsTemplate,
    SettingsValidation,
)


class EnterpriseSettingsService:
    """Service for managing enterprise settings, categories, groups, profiles, and more."""

    def __init__(self, config: SettingsConfig | None = None) -> None:
        """Initialize the enterprise settings service."""
        self._config = config or SettingsConfig()
        self._settings: dict[str, EnterpriseSettings] = {}
        self._categories: dict[SettingsCategory, SettingsCategory] = {}
        self._groups: dict[str, SettingsGroup] = {}
        self._profiles: dict[str, SettingsProfile] = {}
        self._audit_log: list[SettingsAuditEntry] = []
        self._history: list[SettingsHistoryEntry] = []
        self._validations: list[SettingsValidation] = []
        self._templates: dict[str, SettingsTemplate] = {}
        self._overrides: dict[str, SettingsEnvironmentOverride] = {}
        self._permissions: dict[str, SettingsPermission] = {}
        self._notifications: dict[str, SettingsNotification] = {}
        self._definitions: dict[str, SettingsDefinition] = {}
        self._events: list[Any] = []

    def _emit(self, event: Any) -> None:
        """Register an event for later draining."""
        self._events.append(event)

    def drain_events(self) -> list[Any]:
        """Return all pending events and clear the buffer."""
        events = self._events[:]
        self._events.clear()
        return events

    # -- Settings CRUD --------------------------------------------------

    async def create_setting(self, setting: EnterpriseSettings) -> EnterpriseSettings:
        """Create a new enterprise setting."""
        if setting.id in self._settings:
            raise EnterpriseSettingsValidationError(f"Setting '{setting.id}' already exists")
        self._settings[setting.id] = setting
        self._emit(EnterpriseSettingsCreated(setting=setting))
        return setting

    async def get_setting(self, setting_id: str) -> EnterpriseSettings:
        """Get a setting by its ID."""
        setting = self._settings.get(setting_id)
        if setting is None:
            raise EnterpriseSettingsNotFoundError(f"Setting '{setting_id}' not found")
        return setting

    async def update_setting(self, setting_id: str, **updates: Any) -> EnterpriseSettings:
        """Update an existing enterprise setting."""
        existing = await self.get_setting(setting_id)
        old_value = existing.value
        updated = existing.model_copy(update=updates)
        if self._config.enable_versioning:
            updated = updated.model_copy(update={"version": existing.version + 1})
        if self._config.enable_audit:
            self._audit_log.append(
                SettingsAuditEntry(
                    id=str(uuid4()),
                    action="update",
                    entity_type="setting",
                    entity_id=setting_id,
                    old_value=old_value,
                    new_value=updated.value,
                )
            )
        self._settings[setting_id] = updated
        self._emit(EnterpriseSettingsUpdated(setting=updated, old_value=old_value))
        return updated

    async def delete_setting(self, setting_id: str) -> None:
        """Delete an enterprise setting."""
        setting = self._settings.pop(setting_id, None)
        if setting is None:
            raise EnterpriseSettingsNotFoundError(f"Setting '{setting_id}' not found")
        self._emit(EnterpriseSettingsDeleted(setting_id=setting_id, setting_key=setting.key))

    async def list_settings(self) -> list[EnterpriseSettings]:
        """Return all registered enterprise settings."""
        return list(self._settings.values())

    # -- Categories CRUD ------------------------------------------------

    async def create_category(self, category: SettingsCategory) -> SettingsCategory:
        """Create a new settings category."""
        if category in self._categories:
            raise EnterpriseSettingsCategoryError(f"Category '{category.value}' already exists")
        self._categories[category] = category
        self._emit(EnterpriseSettingsCategoryCreated(category=category))
        return category

    async def list_categories(self) -> list[SettingsCategory]:
        """Return all registered categories."""
        return list(self._categories.values())

    async def delete_category(self, category: SettingsCategory) -> None:
        """Delete a settings category."""
        if category not in self._categories:
            raise EnterpriseSettingsCategoryError(f"Category '{category.value}' not found")
        del self._categories[category]
        self._emit(EnterpriseSettingsCategoryDeleted(category=category))

    # -- Groups CRUD ----------------------------------------------------

    async def create_group(self, group: SettingsGroup) -> SettingsGroup:
        """Create a new settings group."""
        if group.id in self._groups:
            raise EnterpriseSettingsValidationError(f"Group '{group.id}' already exists")
        self._groups[group.id] = group
        self._emit(EnterpriseSettingsGroupCreated(group=group))
        return group

    async def list_groups(self) -> list[SettingsGroup]:
        """Return all registered groups."""
        return list(self._groups.values())

    async def delete_group(self, group_id: str) -> None:
        """Delete a settings group."""
        group = self._groups.pop(group_id, None)
        if group is None:
            raise EnterpriseSettingsNotFoundError(f"Group '{group_id}' not found")
        self._emit(EnterpriseSettingsGroupDeleted(group_id=group_id, group_name=group.name))

    # -- Profiles CRUD --------------------------------------------------

    async def create_profile(self, profile: SettingsProfile) -> SettingsProfile:
        """Create a new settings profile."""
        if profile.id in self._profiles:
            raise EnterpriseSettingsValidationError(f"Profile '{profile.id}' already exists")
        self._profiles[profile.id] = profile
        return profile

    async def list_profiles(self) -> list[SettingsProfile]:
        """Return all registered profiles."""
        return list(self._profiles.values())

    async def activate_profile(self, profile_id: str) -> SettingsProfile:
        """Activate a settings profile."""
        profile = self._profiles.get(profile_id)
        if profile is None:
            raise EnterpriseSettingsProfileError(f"Profile '{profile_id}' not found")
        activated = profile.model_copy(update={"is_active": True})
        self._profiles[profile_id] = activated
        self._emit(EnterpriseSettingsProfileActivated(profile=activated))
        return activated

    async def deactivate_profile(self, profile_id: str) -> SettingsProfile:
        """Deactivate a settings profile."""
        profile = self._profiles.get(profile_id)
        if profile is None:
            raise EnterpriseSettingsProfileError(f"Profile '{profile_id}' not found")
        deactivated = profile.model_copy(update={"is_active": False})
        self._profiles[profile_id] = deactivated
        self._emit(
            EnterpriseSettingsProfileDeactivated(
                profile_id=profile_id,
                profile_name=profile.name,
            )
        )
        return deactivated

    # -- Validation -----------------------------------------------------

    async def validate_setting(self, setting_id: str) -> SettingsValidation:
        """Validate a setting by its ID."""
        setting = await self.get_setting(setting_id)
        errors: list[str] = []
        warnings: list[str] = []
        if setting.value is None and setting.key:
            warnings.append(f"Setting '{setting.key}' has no value")
        validation = SettingsValidation(
            id=str(uuid4()),
            setting_id=setting_id,
            valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )
        self._validations.append(validation)
        self._emit(EnterpriseSettingsValidated(validation=validation))
        return validation

    # -- Export / Import ------------------------------------------------

    async def export_settings(
        self,
        categories: tuple[SettingsCategory, ...] = (),
        exported_by: str = "",
    ) -> SettingsExport:
        """Export settings, optionally filtered by category."""
        filtered = (
            [s for s in self._settings.values() if s.category in categories]
            if categories
            else list(self._settings.values())
        )
        export = SettingsExport(
            id=str(uuid4()),
            categories=categories,
            settings={s.key: s.value for s in filtered},
            exported_by=exported_by,
        )
        self._emit(
            EnterpriseSettingsExported(
                export_format=export.format,
                categories=categories,
                exported_by=exported_by,
            )
        )
        return export

    async def import_settings(self, import_data: SettingsImport) -> int:
        """Import settings from an import payload. Returns the number of settings imported."""
        count = 0
        for key, value in import_data.settings.items():
            existing = next((s for s in self._settings.values() if s.key == key), None)
            if existing and import_data.import_mode == "skip":
                continue
            setting = existing or EnterpriseSettings(
                id=str(uuid4()),
                key=key,
                value=value,
            )
            if existing and import_data.import_mode == "merge":
                setting = existing.model_copy(update={"value": value})
            self._settings[setting.id] = setting
            count += 1
        self._emit(
            EnterpriseSettingsImported(
                import_format=import_data.format,
                import_mode=import_data.import_mode,
                imported_by=import_data.imported_by,
            )
        )
        return count

    # -- Templates ------------------------------------------------------

    async def apply_template(
        self,
        template: SettingsTemplate,
        applied_by: str = "",
    ) -> int:
        """Apply a settings template. Returns the number of settings created."""
        count = 0
        for key, value in template.settings.items():
            setting_id = str(uuid4())
            self._settings[setting_id] = EnterpriseSettings(
                id=setting_id,
                key=key,
                value=value,
                category=template.category,
            )
            count += 1
        self._templates[template.id] = template
        self._emit(EnterpriseSettingsTemplateApplied(template=template, applied_by=applied_by))
        return count

    # -- Environment Overrides -------------------------------------------

    async def set_environment_override(
        self,
        override: SettingsEnvironmentOverride,
    ) -> SettingsEnvironmentOverride:
        """Set an environment-specific override for a setting."""
        key = f"{override.setting_key}:{override.environment}"
        self._overrides[key] = override
        self._emit(
            EnterpriseSettingsEnvironmentOverrideSet(
                setting_key=override.setting_key,
                environment=override.environment,
                value=override.value,
                set_by=override.created_by,
            )
        )
        return override

    async def get_environment_override(
        self,
        setting_key: str,
        environment: str,
    ) -> SettingsEnvironmentOverride | None:
        """Get the environment override for a setting, if any."""
        return self._overrides.get(f"{setting_key}:{environment}")

    # -- Audit / History ------------------------------------------------

    async def get_audit_log(self) -> list[SettingsAuditEntry]:
        """Return the audit log entries."""
        return list(self._audit_log)

    async def record_history(
        self,
        setting_id: str,
        setting_key: str = "",
        old_value: Any = None,
        new_value: Any = None,
        changed_by: str = "",
    ) -> SettingsHistoryEntry:
        """Record a history entry for a setting change."""
        entry = SettingsHistoryEntry(
            id=str(uuid4()),
            setting_id=setting_id,
            setting_key=setting_key,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
        )
        self._history.append(entry)
        max_entries = self._config.max_history_entries
        if max_entries > 0 and len(self._history) > max_entries:
            self._history.pop(0)
        self._emit(
            EnterpriseSettingsHistoryRecorded(
                setting_id=setting_id,
                setting_key=setting_key,
                old_value=old_value,
                new_value=new_value,
                changed_by=changed_by,
            )
        )
        return entry

    async def get_history(self) -> list[SettingsHistoryEntry]:
        """Return the history entries."""
        return list(self._history)

    # -- Definitions CRUD -----------------------------------------------

    async def create_definition(
        self,
        definition: SettingsDefinition,
    ) -> SettingsDefinition:
        """Create a new settings definition."""
        if definition.id in self._definitions:
            raise EnterpriseSettingsValidationError(f"Definition '{definition.id}' already exists")
        self._definitions[definition.id] = definition
        return definition

    async def list_definitions(self) -> list[SettingsDefinition]:
        """Return all registered definitions."""
        return list(self._definitions.values())

    # -- Permissions CRUD -----------------------------------------------

    async def set_permission(self, permission: SettingsPermission) -> SettingsPermission:
        """Set a permission for a setting."""
        self._permissions[permission.id] = permission
        return permission

    async def list_permissions(self) -> list[SettingsPermission]:
        """Return all registered permissions."""
        return list(self._permissions.values())

    # -- Notification CRUD ----------------------------------------------

    async def set_notification(self, notification: SettingsNotification) -> SettingsNotification:
        """Set a notification configuration for a setting."""
        self._notifications[notification.id] = notification
        return notification

    async def list_notifications(self) -> list[SettingsNotification]:
        """Return all registered notifications."""
        return list(self._notifications.values())

    # -- Utility --------------------------------------------------------

    async def get_config(self) -> SettingsConfig:
        """Return the module configuration."""
        return self._config


__all__ = ["EnterpriseSettingsService"]
