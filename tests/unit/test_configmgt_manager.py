"""Tests for configmgt manager."""

from __future__ import annotations

import pytest

from eaip.configmgt.exceptions import (
    ConfigNotFoundError,
    ConfigValidationError,
    ProfileNotFoundError,
    SnapshotNotFoundError,
)
from eaip.configmgt.manager import ConfigManager
from eaip.configmgt.models import (
    ConfigEntry,
    ConfigEntrySource,
    ConfigEntryStatus,
    ConfigEntryType,
    ConfigMgtConfig,
    ConfigProfile,
    ConfigProfileStatus,
)


class TestConfigManager:
    @pytest.fixture
    def manager(self) -> ConfigManager:
        config = ConfigMgtConfig(
            enable_audit_logging=True,
            enable_versioning=True,
            enable_hot_reload=False,
            validation_on_update=True,
        )
        return ConfigManager(config=config)

    # --- entries ---

    async def test_set_and_get_entry(self, manager: ConfigManager) -> None:
        entry = ConfigEntry(id="e1", key="db.host", value="localhost")
        await manager.set_entry(entry)
        result = await manager.get_entry("e1")
        assert result.key == "db.host"
        assert result.value == "localhost"

    async def test_get_entry_not_found(self, manager: ConfigManager) -> None:
        with pytest.raises(ConfigNotFoundError):
            await manager.get_entry("nonexistent")

    async def test_set_entry_updates_version(self, manager: ConfigManager) -> None:
        e1 = ConfigEntry(id="e1", key="db.host", value="v1")
        await manager.set_entry(e1)
        e2 = ConfigEntry(id="e1", key="db.host", value="v2")
        result = await manager.set_entry(e2)
        assert result.version == 2

    async def test_delete_entry(self, manager: ConfigManager) -> None:
        entry = ConfigEntry(id="e1", key="k", value="v")
        await manager.set_entry(entry)
        await manager.delete_entry("e1")
        with pytest.raises(ConfigNotFoundError):
            await manager.get_entry("e1")

    async def test_delete_entry_not_found(self, manager: ConfigManager) -> None:
        with pytest.raises(ConfigNotFoundError):
            await manager.delete_entry("nonexistent")

    async def test_list_entries(self, manager: ConfigManager) -> None:
        await manager.set_entry(
            ConfigEntry(id="e1", key="db.host", value="localhost", tags=("prod",))
        )
        await manager.set_entry(ConfigEntry(id="e2", key="db.port", value="5432", tags=("prod",)))
        await manager.set_entry(ConfigEntry(id="e3", key="log.level", value="debug", tags=("dev",)))

        all_ = await manager.list_entries()
        assert len(all_) == 3

        filtered = await manager.list_entries(key_filter="db")
        assert len(filtered) == 2

        tagged = await manager.list_entries(tag_filter="dev")
        assert len(tagged) == 1

    async def test_list_entries_with_filters(self, manager: ConfigManager) -> None:
        await manager.set_entry(
            ConfigEntry(
                id="e1",
                key="k1",
                value="1",
                type=ConfigEntryType.INTEGER,
                source=ConfigEntrySource.FILE,
                status=ConfigEntryStatus.ACTIVE,
            )
        )
        await manager.set_entry(
            ConfigEntry(
                id="e2",
                key="k2",
                value="x",
                type=ConfigEntryType.STRING,
                source=ConfigEntrySource.ENV,
                status=ConfigEntryStatus.DEPRECATED,
            )
        )

        assert len(await manager.list_entries(type_filter=ConfigEntryType.INTEGER)) == 1
        assert len(await manager.list_entries(source_filter=ConfigEntrySource.ENV)) == 1
        assert len(await manager.list_entries(status_filter=ConfigEntryStatus.DEPRECATED)) == 1

    # --- profiles ---

    async def test_create_and_get_profile(self, manager: ConfigManager) -> None:
        profile = ConfigProfile(id="p1", name="Production", environment="prod")
        await manager.create_profile(profile)
        result = await manager.get_profile("p1")
        assert result.name == "Production"
        assert result.environment == "prod"

    async def test_get_profile_not_found(self, manager: ConfigManager) -> None:
        with pytest.raises(ProfileNotFoundError):
            await manager.get_profile("nonexistent")

    async def test_update_profile(self, manager: ConfigManager) -> None:
        p = ConfigProfile(id="p1", name="Original", entries={"k": "v"})
        await manager.create_profile(p)
        updated = ConfigProfile(id="p1", name="Updated", entries={"k": "v2"})
        result = await manager.update_profile(updated)
        assert result.name == "Updated"
        assert result.entries == {"k": "v2"}

    async def test_update_profile_not_found(self, manager: ConfigManager) -> None:
        with pytest.raises(ProfileNotFoundError):
            await manager.update_profile(ConfigProfile(id="x", name="X"))

    async def test_delete_profile(self, manager: ConfigManager) -> None:
        await manager.create_profile(ConfigProfile(id="p1", name="P1"))
        await manager.delete_profile("p1")
        with pytest.raises(ProfileNotFoundError):
            await manager.get_profile("p1")

    async def test_delete_profile_not_found(self, manager: ConfigManager) -> None:
        with pytest.raises(ProfileNotFoundError):
            await manager.delete_profile("nonexistent")

    async def test_list_profiles(self, manager: ConfigManager) -> None:
        await manager.create_profile(ConfigProfile(id="p1", name="Prod", environment="prod"))
        await manager.create_profile(ConfigProfile(id="p2", name="Dev", environment="dev"))
        await manager.create_profile(
            ConfigProfile(
                id="p3",
                name="Inactive",
                environment="prod",
                status=ConfigProfileStatus.INACTIVE,
            )
        )

        assert len(await manager.list_profiles()) == 3
        assert len(await manager.list_profiles(environment="prod")) == 2
        assert len(await manager.list_profiles(environment="dev")) == 1
        assert len(await manager.list_profiles(status_filter=ConfigProfileStatus.INACTIVE)) == 1

    # --- effective resolution ---

    async def test_get_effective_direct(self, manager: ConfigManager) -> None:
        profile = ConfigProfile(id="p1", name="Prod", entries={"key1": "val1"})
        await manager.create_profile(profile)
        val = await manager.get_effective("p1", "key1")
        assert val == "val1"

    async def test_get_effective_nonexistent_key(self, manager: ConfigManager) -> None:
        profile = ConfigProfile(id="p1", name="Prod")
        await manager.create_profile(profile)
        val = await manager.get_effective("p1", "unknown")
        assert val is None

    async def test_get_effective_inherits_parent(self, manager: ConfigManager) -> None:
        base = ConfigProfile(
            id="base", name="Base", entries={"key1": "base_val", "key2": "base_val"}
        )
        child = ConfigProfile(
            id="child", name="Child", entries={"key1": "child_val"}, parent_profile="base"
        )
        await manager.create_profile(base)
        await manager.create_profile(child)

        assert await manager.get_effective("child", "key1") == "child_val"
        assert await manager.get_effective("child", "key2") == "base_val"

    async def test_get_all_effective(self, manager: ConfigManager) -> None:
        base = ConfigProfile(id="base", name="Base", entries={"a": "1", "b": "2"})
        child = ConfigProfile(
            id="child", name="Child", entries={"b": "overridden", "c": "3"}, parent_profile="base"
        )
        await manager.create_profile(base)
        await manager.create_profile(child)

        effective = await manager.get_all_effective("child")
        assert effective == {"a": "1", "b": "overridden", "c": "3"}

    async def test_apply_profile_creates_entries(self, manager: ConfigManager) -> None:
        profile = ConfigProfile(id="p1", name="Prod", entries={"k1": "v1", "k2": "v2"})
        await manager.create_profile(profile)
        applied = await manager.apply_profile("p1")
        assert applied == 2
        assert (await manager.get_entry("auto_k1")).value == "v1"

    async def test_apply_profile_updates_existing(self, manager: ConfigManager) -> None:
        await manager.set_entry(ConfigEntry(id="auto_k1", key="k1", value="old"))
        profile = ConfigProfile(id="p1", name="Prod", entries={"k1": "new"})
        await manager.create_profile(profile)
        applied = await manager.apply_profile("p1")
        assert applied == 1
        assert (await manager.get_entry("auto_k1")).value == "new"

    # --- validation failure ---

    async def test_set_entry_validation_failure(self, manager: ConfigManager) -> None:
        entry = ConfigEntry(id="e1", key="k", value="not_int", type=ConfigEntryType.INTEGER)
        await manager.set_entry(entry)
        with pytest.raises(ConfigValidationError):
            await manager.set_entry(
                ConfigEntry(id="e1", key="k", value="still_bad", type=ConfigEntryType.INTEGER)
            )

    # --- snapshots ---

    async def test_create_snapshot(self, manager: ConfigManager) -> None:
        profile = ConfigProfile(id="p1", name="Prod", entries={"k": "v"})
        await manager.create_profile(profile)
        snapshot = await manager.create_snapshot("p1")
        assert snapshot.profile_id == "p1"
        assert snapshot.entries == {"k": "v"}
        assert snapshot.checksum != ""

    async def test_restore_snapshot(self, manager: ConfigManager) -> None:
        profile = ConfigProfile(id="p1", name="Prod", entries={"k": "v1"})
        await manager.create_profile(profile)
        snapshot = await manager.create_snapshot("p1")

        updated = ConfigProfile(id="p1", name="Prod", entries={"k": "v2"})
        await manager.update_profile(updated)

        restored = await manager.restore_snapshot(snapshot.id)
        assert restored == 1
        assert (await manager.get_profile("p1")).entries == {"k": "v1"}

    async def test_restore_snapshot_not_found(self, manager: ConfigManager) -> None:
        with pytest.raises(SnapshotNotFoundError):
            await manager.restore_snapshot("nonexistent")

    async def test_diff_snapshots(self, manager: ConfigManager) -> None:
        profile = ConfigProfile(id="p1", name="Prod", entries={"a": "1", "b": "2"})
        await manager.create_profile(profile)
        snap_a = await manager.create_snapshot("p1")

        await manager.update_profile(
            ConfigProfile(id="p1", name="Prod", entries={"a": "10", "c": "3"})
        )
        snap_b = await manager.create_snapshot("p1")

        diff = await manager.diff_snapshots(snap_a.id, snap_b.id)
        assert "a" in diff
        assert diff["a"]["old"] == "1"
        assert diff["a"]["new"] == "10"
        assert "b" in diff
        assert diff["b"]["new"] is None
        assert "c" in diff
        assert diff["c"]["old"] is None

    async def test_diff_snapshots_not_found(self, manager: ConfigManager) -> None:
        profile = ConfigProfile(id="p1", name="Prod")
        await manager.create_profile(profile)
        snap = await manager.create_snapshot("p1")
        with pytest.raises(SnapshotNotFoundError):
            await manager.diff_snapshots("nonexistent", snap.id)
        with pytest.raises(SnapshotNotFoundError):
            await manager.diff_snapshots(snap.id, "nonexistent")

    async def test_max_snapshots_enforced(self, manager: ConfigManager) -> None:
        config = ConfigMgtConfig(max_snapshots=2)
        mgr = ConfigManager(config=config)
        profile = ConfigProfile(id="p1", name="P1", entries={"k": "v"})
        await mgr.create_profile(profile)
        snap1 = await mgr.create_snapshot("p1")
        snap2 = await mgr.create_snapshot("p1")
        snap3 = await mgr.create_snapshot("p1")

        assert snap1.id not in mgr._snapshots
        assert snap2.id in mgr._snapshots
        assert snap3.id in mgr._snapshots
        assert len([s for s in mgr._snapshots.values() if s.profile_id == "p1"]) == 2

    # --- events ---

    async def test_events_emitted_on_create(self, manager: ConfigManager) -> None:
        entry = ConfigEntry(id="e1", key="k", value="v")
        await manager.set_entry(entry)
        assert any(e.__class__.__name__ == "ConfigCreated" for e in manager.events)

    async def test_events_emitted_on_update(self, manager: ConfigManager) -> None:
        entry = ConfigEntry(id="e1", key="k", value="v1")
        await manager.set_entry(entry)
        manager._clear_events()
        await manager.set_entry(ConfigEntry(id="e1", key="k", value="v2"))
        assert any(e.__class__.__name__ == "ConfigUpdated" for e in manager.events)

    async def test_events_emitted_on_delete(self, manager: ConfigManager) -> None:
        entry = ConfigEntry(id="e1", key="k", value="v")
        await manager.set_entry(entry)
        manager._clear_events()
        await manager.delete_entry("e1")
        assert any(e.__class__.__name__ == "ConfigDeleted" for e in manager.events)

    # --- changes ---

    async def test_list_changes(self, manager: ConfigManager) -> None:
        e1 = ConfigEntry(id="e1", key="k", value="v1")
        await manager.set_entry(e1)
        await manager.set_entry(ConfigEntry(id="e1", key="k", value="v2"))

        changes = await manager.list_changes(entry_id="e1")
        assert len(changes) == 1
        assert changes[0].old_value == "v1"
        assert changes[0].new_value == "v2"
