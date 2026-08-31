"""Tests for the enterprise settings module."""

from __future__ import annotations

from uuid import uuid4

import pytest

from eaip.enterprise_settings.events import (
    EnterpriseSettingsCategoryCreated,
    EnterpriseSettingsCategoryDeleted,
    EnterpriseSettingsCreated,
    EnterpriseSettingsDeleted,
    EnterpriseSettingsEnvironmentOverrideSet,
    EnterpriseSettingsExported,
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
    SettingsCategory,
    SettingsConfig,
    SettingsDefinition,
    SettingsEnvironmentOverride,
    SettingsGroup,
    SettingsImport,
    SettingsNotification,
    SettingsPermission,
    SettingsProfile,
    SettingsScope,
    SettingsTemplate,
)
from eaip.enterprise_settings.service import EnterpriseSettingsService


@pytest.fixture
def service() -> EnterpriseSettingsService:
    return EnterpriseSettingsService()


@pytest.fixture
def sample_setting() -> EnterpriseSettings:
    return EnterpriseSettings(
        id="s1",
        key="feature_x.enabled",
        value=True,
        category=SettingsCategory.GENERAL,
        scope=SettingsScope.GLOBAL,
    )


# -- Settings CRUD ---------------------------------------------------------


class TestSettingsCRUD:
    async def test_create_setting(
        self, service: EnterpriseSettingsService, sample_setting: EnterpriseSettings
    ) -> None:
        result = await service.create_setting(sample_setting)
        assert result.id == "s1"
        assert result.key == "feature_x.enabled"
        assert result.value is True

    async def test_create_duplicate_raises(
        self, service: EnterpriseSettingsService, sample_setting: EnterpriseSettings
    ) -> None:
        await service.create_setting(sample_setting)
        with pytest.raises(EnterpriseSettingsValidationError):
            await service.create_setting(sample_setting)

    async def test_get_setting(
        self, service: EnterpriseSettingsService, sample_setting: EnterpriseSettings
    ) -> None:
        await service.create_setting(sample_setting)
        result = await service.get_setting("s1")
        assert result.key == "feature_x.enabled"

    async def test_get_setting_not_found(self, service: EnterpriseSettingsService) -> None:
        with pytest.raises(EnterpriseSettingsNotFoundError):
            await service.get_setting("nonexistent")

    async def test_update_setting(
        self, service: EnterpriseSettingsService, sample_setting: EnterpriseSettings
    ) -> None:
        await service.create_setting(sample_setting)
        updated = await service.update_setting("s1", value=False)
        assert updated.value is False
        assert updated.version == 2

    async def test_update_setting_not_found(self, service: EnterpriseSettingsService) -> None:
        with pytest.raises(EnterpriseSettingsNotFoundError):
            await service.update_setting("nonexistent", value=1)

    async def test_delete_setting(
        self, service: EnterpriseSettingsService, sample_setting: EnterpriseSettings
    ) -> None:
        await service.create_setting(sample_setting)
        await service.delete_setting("s1")
        assert len(await service.list_settings()) == 0

    async def test_delete_setting_not_found(self, service: EnterpriseSettingsService) -> None:
        with pytest.raises(EnterpriseSettingsNotFoundError):
            await service.delete_setting("nonexistent")

    async def test_list_settings(self, service: EnterpriseSettingsService) -> None:
        s1 = EnterpriseSettings(id="s1", key="a", value=1)
        s2 = EnterpriseSettings(id="s2", key="b", value=2)
        await service.create_setting(s1)
        await service.create_setting(s2)
        settings = await service.list_settings()
        assert len(settings) == 2


# -- Categories --------------------------------------------------------------


class TestCategories:
    async def test_create_category(self, service: EnterpriseSettingsService) -> None:
        result = await service.create_category(SettingsCategory.SECURITY)
        assert result == SettingsCategory.SECURITY

    async def test_create_duplicate_category_raises(
        self, service: EnterpriseSettingsService
    ) -> None:
        await service.create_category(SettingsCategory.SECURITY)
        with pytest.raises(EnterpriseSettingsCategoryError):
            await service.create_category(SettingsCategory.SECURITY)

    async def test_list_categories(self, service: EnterpriseSettingsService) -> None:
        await service.create_category(SettingsCategory.GENERAL)
        await service.create_category(SettingsCategory.SECURITY)
        cats = await service.list_categories()
        assert len(cats) == 2

    async def test_delete_category(self, service: EnterpriseSettingsService) -> None:
        await service.create_category(SettingsCategory.AUDIT)
        await service.delete_category(SettingsCategory.AUDIT)
        assert len(await service.list_categories()) == 0


# -- Groups ------------------------------------------------------------------


class TestGroups:
    async def test_create_group(self, service: EnterpriseSettingsService) -> None:
        group = SettingsGroup(id="g1", name="Security Settings", category=SettingsCategory.SECURITY)
        result = await service.create_group(group)
        assert result.name == "Security Settings"

    async def test_list_groups(self, service: EnterpriseSettingsService) -> None:
        await service.create_group(SettingsGroup(id="g1", name="G1"))
        await service.create_group(SettingsGroup(id="g2", name="G2"))
        assert len(await service.list_groups()) == 2

    async def test_delete_group(self, service: EnterpriseSettingsService) -> None:
        await service.create_group(SettingsGroup(id="g1", name="G1"))
        await service.delete_group("g1")
        assert len(await service.list_groups()) == 0

    async def test_delete_group_not_found(self, service: EnterpriseSettingsService) -> None:
        with pytest.raises(EnterpriseSettingsNotFoundError):
            await service.delete_group("nonexistent")


# -- Profiles ----------------------------------------------------------------


class TestProfiles:
    async def test_create_profile(self, service: EnterpriseSettingsService) -> None:
        profile = SettingsProfile(id="p1", name="Production", overrides={"debug": False})
        result = await service.create_profile(profile)
        assert result.name == "Production"

    async def test_activate_profile(self, service: EnterpriseSettingsService) -> None:
        profile = SettingsProfile(id="p1", name="Prod", is_active=False)
        await service.create_profile(profile)
        activated = await service.activate_profile("p1")
        assert activated.is_active is True

    async def test_deactivate_profile(self, service: EnterpriseSettingsService) -> None:
        profile = SettingsProfile(id="p1", name="Prod", is_active=True)
        await service.create_profile(profile)
        deactivated = await service.deactivate_profile("p1")
        assert deactivated.is_active is False

    async def test_activate_profile_not_found(self, service: EnterpriseSettingsService) -> None:
        with pytest.raises(EnterpriseSettingsProfileError):
            await service.activate_profile("nonexistent")


# -- Validation --------------------------------------------------------------


class TestValidation:
    async def test_validate_setting(
        self, service: EnterpriseSettingsService, sample_setting: EnterpriseSettings
    ) -> None:
        await service.create_setting(sample_setting)
        result = await service.validate_setting("s1")
        assert result.setting_id == "s1"
        assert result.valid is True

    async def test_validate_setting_not_found(self, service: EnterpriseSettingsService) -> None:
        with pytest.raises(EnterpriseSettingsNotFoundError):
            await service.validate_setting("nonexistent")


# -- Export / Import --------------------------------------------------------


class TestExportImport:
    async def test_export_settings(
        self, service: EnterpriseSettingsService, sample_setting: EnterpriseSettings
    ) -> None:
        await service.create_setting(sample_setting)
        export = await service.export_settings()
        assert export.settings.get("feature_x.enabled") is True

    async def test_import_settings(self, service: EnterpriseSettingsService) -> None:
        import_data = SettingsImport(
            id=str(uuid4()),
            settings={"new.key": "imported_value"},
        )
        count = await service.import_settings(import_data)
        assert count == 1
        settings = await service.list_settings()
        assert any(s.key == "new.key" for s in settings)

    async def test_export_emits_event(self, service: EnterpriseSettingsService) -> None:
        await service.export_settings()
        events = service.drain_events()
        assert any(isinstance(e, EnterpriseSettingsExported) for e in events)

    async def test_import_emits_event(self, service: EnterpriseSettingsService) -> None:
        import_data = SettingsImport(id=str(uuid4()), settings={"k": "v"})
        await service.import_settings(import_data)
        events = service.drain_events()
        assert any(isinstance(e, EnterpriseSettingsImported) for e in events)


# -- Templates ---------------------------------------------------------------


class TestTemplates:
    async def test_apply_template(self, service: EnterpriseSettingsService) -> None:
        template = SettingsTemplate(
            id="t1",
            name="Compliance Baseline",
            category=SettingsCategory.COMPLIANCE,
            settings={"audit.enabled": True, "retention.days": 90},
        )
        count = await service.apply_template(template)
        assert count == 2

    async def test_apply_template_emits_event(self, service: EnterpriseSettingsService) -> None:
        template = SettingsTemplate(id="t1", name="T1", settings={"k": "v"})
        await service.apply_template(template)
        events = service.drain_events()
        assert any(isinstance(e, EnterpriseSettingsTemplateApplied) for e in events)


# -- Environment Overrides --------------------------------------------------


class TestEnvironmentOverrides:
    async def test_set_override(self, service: EnterpriseSettingsService) -> None:
        override = SettingsEnvironmentOverride(
            id="o1",
            setting_key="feature_x.enabled",
            environment="staging",
            value=False,
        )
        result = await service.set_environment_override(override)
        assert result.value is False

    async def test_get_override(self, service: EnterpriseSettingsService) -> None:
        override = SettingsEnvironmentOverride(
            id="o1",
            setting_key="feature_x.enabled",
            environment="staging",
            value=True,
        )
        await service.set_environment_override(override)
        result = await service.get_environment_override("feature_x.enabled", "staging")
        assert result is not None
        assert result.value is True

    async def test_get_override_not_found(self, service: EnterpriseSettingsService) -> None:
        result = await service.get_environment_override("missing", "prod")
        assert result is None


# -- Audit / History --------------------------------------------------------


class TestAuditHistory:
    async def test_update_triggers_audit(
        self, service: EnterpriseSettingsService, sample_setting: EnterpriseSettings
    ) -> None:
        await service.create_setting(sample_setting)
        await service.update_setting("s1", value=False)
        audit = await service.get_audit_log()
        assert len(audit) == 1
        assert audit[0].entity_id == "s1"

    async def test_record_history(self, service: EnterpriseSettingsService) -> None:
        entry = await service.record_history(
            setting_id="s1",
            setting_key="feature_x.enabled",
            old_value=True,
            new_value=False,
            changed_by="admin",
        )
        assert entry.setting_key == "feature_x.enabled"
        history = await service.get_history()
        assert len(history) == 1

    async def test_history_max_entries(self, service: EnterpriseSettingsService) -> None:
        config = SettingsConfig(max_history_entries=3)
        svc = EnterpriseSettingsService(config=config)
        for i in range(5):
            await svc.record_history(setting_id=f"s{i}", setting_key=f"k{i}")
        assert len(await svc.get_history()) == 3


# -- Definitions ------------------------------------------------------------


class TestDefinitions:
    async def test_create_definition(self, service: EnterpriseSettingsService) -> None:
        definition = SettingsDefinition(
            id="d1",
            key="max_retries",
            value_type="int",
            default_value=3,
        )
        result = await service.create_definition(definition)
        assert result.key == "max_retries"

    async def test_list_definitions(self, service: EnterpriseSettingsService) -> None:
        await service.create_definition(SettingsDefinition(id="d1", key="k1"))
        await service.create_definition(SettingsDefinition(id="d2", key="k2"))
        assert len(await service.list_definitions()) == 2


# -- Permissions ------------------------------------------------------------


class TestPermissions:
    async def test_set_permission(self, service: EnterpriseSettingsService) -> None:
        perm = SettingsPermission(
            id="perm1", setting_key="secret.key", can_read=True, can_write=False
        )
        result = await service.set_permission(perm)
        assert result.can_read is True
        assert result.can_write is False

    async def test_list_permissions(self, service: EnterpriseSettingsService) -> None:
        await service.set_permission(SettingsPermission(id="p1", setting_key="k1"))
        await service.set_permission(SettingsPermission(id="p2", setting_key="k2"))
        assert len(await service.list_permissions()) == 2


# -- Notifications ----------------------------------------------------------


class TestNotifications:
    async def test_set_notification(self, service: EnterpriseSettingsService) -> None:
        notif = SettingsNotification(
            id="n1",
            setting_key="feature_x.enabled",
            event="update",
            channel="slack",
            recipients=("#team",),
        )
        result = await service.set_notification(notif)
        assert result.channel == "slack"

    async def test_list_notifications(self, service: EnterpriseSettingsService) -> None:
        await service.set_notification(
            SettingsNotification(id="n1", setting_key="k1", event="update", channel="email")
        )
        await service.set_notification(
            SettingsNotification(id="n2", setting_key="k2", event="update", channel="sms")
        )
        assert len(await service.list_notifications()) == 2


# -- Events ------------------------------------------------------------------


class TestEvents:
    async def test_create_setting_emits_event(
        self, service: EnterpriseSettingsService, sample_setting: EnterpriseSettings
    ) -> None:
        await service.create_setting(sample_setting)
        events = service.drain_events()
        assert any(isinstance(e, EnterpriseSettingsCreated) for e in events)

    async def test_delete_setting_emits_event(
        self, service: EnterpriseSettingsService, sample_setting: EnterpriseSettings
    ) -> None:
        await service.create_setting(sample_setting)
        service.drain_events()
        await service.delete_setting("s1")
        events = service.drain_events()
        assert any(isinstance(e, EnterpriseSettingsDeleted) for e in events)

    async def test_update_setting_emits_event(
        self, service: EnterpriseSettingsService, sample_setting: EnterpriseSettings
    ) -> None:
        await service.create_setting(sample_setting)
        service.drain_events()
        await service.update_setting("s1", value=False)
        events = service.drain_events()
        assert any(isinstance(e, EnterpriseSettingsUpdated) for e in events)

    async def test_validate_setting_emits_event(
        self, service: EnterpriseSettingsService, sample_setting: EnterpriseSettings
    ) -> None:
        await service.create_setting(sample_setting)
        service.drain_events()
        await service.validate_setting("s1")
        events = service.drain_events()
        assert any(isinstance(e, EnterpriseSettingsValidated) for e in events)

    async def test_category_created_emits_event(self, service: EnterpriseSettingsService) -> None:
        await service.create_category(SettingsCategory.SECURITY)
        events = service.drain_events()
        assert any(isinstance(e, EnterpriseSettingsCategoryCreated) for e in events)

    async def test_category_deleted_emits_event(self, service: EnterpriseSettingsService) -> None:
        await service.create_category(SettingsCategory.SECURITY)
        service.drain_events()
        await service.delete_category(SettingsCategory.SECURITY)
        events = service.drain_events()
        assert any(isinstance(e, EnterpriseSettingsCategoryDeleted) for e in events)

    async def test_profile_activated_emits_event(self, service: EnterpriseSettingsService) -> None:
        profile = SettingsProfile(id="p1", name="Prod", is_active=False)
        await service.create_profile(profile)
        service.drain_events()
        await service.activate_profile("p1")
        events = service.drain_events()
        assert any(isinstance(e, EnterpriseSettingsProfileActivated) for e in events)

    async def test_history_recording_emits_event(self, service: EnterpriseSettingsService) -> None:
        await service.record_history(setting_id="s1", setting_key="k1")
        events = service.drain_events()
        assert any(isinstance(e, EnterpriseSettingsHistoryRecorded) for e in events)

    async def test_environment_override_emits_event(
        self, service: EnterpriseSettingsService
    ) -> None:
        override = SettingsEnvironmentOverride(
            id="o1", setting_key="k1", environment="dev", value=1
        )
        await service.set_environment_override(override)
        events = service.drain_events()
        assert any(isinstance(e, EnterpriseSettingsEnvironmentOverrideSet) for e in events)

    async def test_event_type_strings(self) -> None:
        expected = [
            ("eaip.enterprise_settings.created", EnterpriseSettingsCreated),
            ("eaip.enterprise_settings.updated", EnterpriseSettingsUpdated),
            ("eaip.enterprise_settings.deleted", EnterpriseSettingsDeleted),
            ("eaip.enterprise_settings.category.created", EnterpriseSettingsCategoryCreated),
            ("eaip.enterprise_settings.category.deleted", EnterpriseSettingsCategoryDeleted),
            ("eaip.enterprise_settings.profile.activated", EnterpriseSettingsProfileActivated),
            ("eaip.enterprise_settings.profile.deactivated", EnterpriseSettingsProfileDeactivated),
            ("eaip.enterprise_settings.exported", EnterpriseSettingsExported),
            ("eaip.enterprise_settings.imported", EnterpriseSettingsImported),
            ("eaip.enterprise_settings.validated", EnterpriseSettingsValidated),
            ("eaip.enterprise_settings.template_applied", EnterpriseSettingsTemplateApplied),
            (
                "eaip.enterprise_settings.environment_override_set",
                EnterpriseSettingsEnvironmentOverrideSet,
            ),
        ]
        for expected_type, event_cls in expected:
            assert event_cls.event_type == expected_type
