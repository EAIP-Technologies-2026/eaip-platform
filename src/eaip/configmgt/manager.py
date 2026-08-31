"""Config manager — entries, profiles, snapshots, and effective-resolution."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from eaip.configmgt.events import (
    ConfigCreated,
    ConfigDeleted,
    ConfigProfileApplied,
    ConfigProfileCreated,
    ConfigSnapshotCreated,
    ConfigUpdated,
    ConfigValidated,
    ConfigValidationFailed,
)
from eaip.configmgt.exceptions import (
    ConfigNotFoundError,
    ConfigValidationError,
    ProfileNotFoundError,
    SnapshotNotFoundError,
)
from eaip.configmgt.models import (
    ConfigChange,
    ConfigEntry,
    ConfigEntrySource,
    ConfigEntryStatus,
    ConfigEntryType,
    ConfigMgtConfig,
    ConfigProfile,
    ConfigProfileStatus,
    ConfigSnapshot,
)
from eaip.configmgt.validation import ConfigValidator
from eaip.configmgt.watcher import ConfigWatcher
from eaip.shared.time import utc_now


class ConfigManager:
    def __init__(
        self,
        config: ConfigMgtConfig | None = None,
        validator: ConfigValidator | None = None,
        watcher: ConfigWatcher | None = None,
    ) -> None:
        self._config = config or ConfigMgtConfig()
        self._validator = validator or ConfigValidator()
        self._watcher = watcher or ConfigWatcher()
        self._entries: dict[str, ConfigEntry] = {}
        self._profiles: dict[str, ConfigProfile] = {}
        self._snapshots: dict[str, ConfigSnapshot] = {}
        self._changes: list[ConfigChange] = []
        self._events: list[Any] = []

    @property
    def events(self) -> list[Any]:
        return list(self._events)

    def _clear_events(self) -> None:
        self._events.clear()

    # --- entries ---

    async def get_entry(self, entry_id: str) -> ConfigEntry:
        entry = self._entries.get(entry_id)
        if entry is None:
            raise ConfigNotFoundError(f"Config entry not found: {entry_id}")
        return entry

    async def set_entry(
        self, entry: ConfigEntry, changed_by: str = "", reason: str = ""
    ) -> ConfigEntry:
        existing = self._entries.get(entry.id)

        if existing is not None:
            old_value = existing.value
            updated = ConfigEntry(
                id=entry.id,
                key=entry.key,
                value=entry.value,
                type=entry.type,
                description=entry.description,
                tags=entry.tags,
                source=entry.source,
                version=existing.version + 1
                if self._config.enable_versioning
                else existing.version,
                status=entry.status,
                created_at=existing.created_at,
                updated_at=utc_now(),
                metadata=entry.metadata,
            )
            self._entries[entry.id] = updated

            if self._config.validation_on_update:
                validation = await self._validator.validate(updated)
                if not validation.valid:
                    self._events.append(
                        ConfigValidationFailed(
                            entry_id=entry.id,
                            entry_key=entry.key,
                            errors=validation.errors,
                        )
                    )
                    raise ConfigValidationError(
                        f"Validation failed for {entry.key}: {', '.join(validation.errors)}",
                    )
                self._events.append(
                    ConfigValidated(
                        entry_id=entry.id,
                        valid=True,
                        errors=(),
                    )
                )

            change = ConfigChange(
                id=f"chg_{entry.id}_{updated.version}",
                entry_id=entry.id,
                old_value=old_value,
                new_value=entry.value,
                changed_by=changed_by,
                reason=reason,
                timestamp=utc_now(),
            )
            self._changes.append(change)

            if self._config.enable_hot_reload:
                await self._watcher.notify_watchers(change)

            self._events.append(
                ConfigUpdated(
                    entry=updated,
                    old_value=old_value,
                    changed_by=changed_by,
                )
            )
            return updated

        self._entries[entry.id] = entry
        self._events.append(ConfigCreated(entry=entry))
        return entry

    async def delete_entry(self, entry_id: str) -> None:
        entry = await self.get_entry(entry_id)
        del self._entries[entry_id]
        self._events.append(ConfigDeleted(entry_id=entry_id, entry_key=entry.key))

    async def list_entries(
        self,
        key_filter: str | None = None,
        type_filter: ConfigEntryType | None = None,
        status_filter: ConfigEntryStatus | None = None,
        source_filter: ConfigEntrySource | None = None,
        tag_filter: str | None = None,
    ) -> list[ConfigEntry]:
        result = list(self._entries.values())
        if key_filter:
            result = [e for e in result if key_filter.lower() in e.key.lower()]
        if type_filter:
            result = [e for e in result if e.type is type_filter]
        if status_filter:
            result = [e for e in result if e.status is status_filter]
        if source_filter:
            result = [e for e in result if e.source is source_filter]
        if tag_filter:
            result = [e for e in result if tag_filter in e.tags]
        return result

    # --- profiles ---

    async def create_profile(self, profile: ConfigProfile) -> ConfigProfile:
        self._profiles[profile.id] = profile
        self._events.append(ConfigProfileCreated(profile=profile))
        return profile

    async def update_profile(self, profile: ConfigProfile) -> ConfigProfile:
        existing = self._profiles.get(profile.id)
        if existing is None:
            raise ProfileNotFoundError(f"Profile not found: {profile.id}")
        updated = ConfigProfile(
            id=profile.id,
            name=profile.name,
            environment=profile.environment,
            entries=profile.entries,
            parent_profile=profile.parent_profile,
            status=profile.status,
            created_at=existing.created_at,
            updated_at=utc_now(),
            metadata=profile.metadata,
        )
        self._profiles[profile.id] = updated
        return updated

    async def delete_profile(self, profile_id: str) -> None:
        if profile_id not in self._profiles:
            raise ProfileNotFoundError(f"Profile not found: {profile_id}")
        del self._profiles[profile_id]

    async def get_profile(self, profile_id: str) -> ConfigProfile:
        profile = self._profiles.get(profile_id)
        if profile is None:
            raise ProfileNotFoundError(f"Profile not found: {profile_id}")
        return profile

    async def list_profiles(
        self,
        environment: str | None = None,
        status_filter: ConfigProfileStatus | None = None,
    ) -> list[ConfigProfile]:
        result = list(self._profiles.values())
        if environment:
            result = [p for p in result if p.environment == environment]
        if status_filter:
            result = [p for p in result if p.status is status_filter]
        return result

    # --- effective resolution ---

    async def get_effective(self, profile_id: str, key: str) -> str | None:
        profile = await self.get_profile(profile_id)
        if key in profile.entries:
            return profile.entries[key]
        if profile.parent_profile:
            return await self.get_effective(profile.parent_profile, key)
        return None

    async def get_all_effective(self, profile_id: str) -> dict[str, str]:
        profile = await self.get_profile(profile_id)
        merged: dict[str, str] = {}
        if profile.parent_profile:
            merged = await self.get_all_effective(profile.parent_profile)
        merged.update(profile.entries)
        return merged

    async def apply_profile(self, profile_id: str) -> int:
        profile = await self.get_profile(profile_id)
        effective = await self.get_all_effective(profile_id)
        applied = 0
        for key, value in effective.items():
            entry_id = f"auto_{key}"
            if entry_id in self._entries:
                existing = self._entries[entry_id]
                if existing.value != value:
                    updated = ConfigEntry(
                        id=entry_id,
                        key=key,
                        value=value,
                        type=existing.type,
                        description=existing.description,
                        tags=existing.tags,
                        source=ConfigEntrySource.API,
                        version=existing.version + 1,
                        status=existing.status,
                        created_at=existing.created_at,
                        updated_at=utc_now(),
                        metadata=existing.metadata,
                    )
                    self._entries[entry_id] = updated
                    applied += 1
            else:
                entry = ConfigEntry(
                    id=entry_id,
                    key=key,
                    value=value,
                    type=ConfigEntryType.STRING,
                    source=ConfigEntrySource.API,
                )
                self._entries[entry_id] = entry
                applied += 1

        if applied > 0:
            self._events.append(
                ConfigProfileApplied(
                    profile_id=profile_id,
                    profile_name=profile.name,
                    entries_count=applied,
                )
            )
        return applied

    # --- snapshots ---

    async def create_snapshot(self, profile_id: str) -> ConfigSnapshot:
        profile = await self.get_profile(profile_id)
        entries = deepcopy(profile.entries)
        checksum = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()

        snapshot = ConfigSnapshot(
            id=f"snap_{profile_id}_{utc_now().isoformat()}",
            profile_id=profile_id,
            entries=entries,
            checksum=checksum,
            created_at=utc_now(),
        )

        profile_snapshots = [s for s in self._snapshots.values() if s.profile_id == profile_id]
        if len(profile_snapshots) >= self._config.max_snapshots:
            oldest = min(profile_snapshots, key=lambda s: s.created_at)
            del self._snapshots[oldest.id]

        self._snapshots[snapshot.id] = snapshot
        self._events.append(ConfigSnapshotCreated(snapshot=snapshot))
        return snapshot

    async def restore_snapshot(self, snapshot_id: str) -> int:
        snapshot = self._snapshots.get(snapshot_id)
        if snapshot is None:
            raise SnapshotNotFoundError(f"Snapshot not found: {snapshot_id}")
        profile = await self.get_profile(snapshot.profile_id)
        restored = ConfigProfile(
            id=profile.id,
            name=profile.name,
            environment=profile.environment,
            entries=snapshot.entries,
            parent_profile=profile.parent_profile,
            status=profile.status,
            created_at=profile.created_at,
            updated_at=utc_now(),
            metadata=profile.metadata,
        )
        self._profiles[profile.id] = restored
        return len(snapshot.entries)

    async def diff_snapshots(
        self, snap_a_id: str, snap_b_id: str
    ) -> dict[str, dict[str, str | None]]:
        snap_a = self._snapshots.get(snap_a_id)
        snap_b = self._snapshots.get(snap_b_id)
        if snap_a is None:
            raise SnapshotNotFoundError(f"Snapshot not found: {snap_a_id}")
        if snap_b is None:
            raise SnapshotNotFoundError(f"Snapshot not found: {snap_b_id}")

        diff: dict[str, dict[str, str | None]] = {}
        all_keys = set(snap_a.entries) | set(snap_b.entries)
        for key in all_keys:
            val_a = snap_a.entries.get(key)
            val_b = snap_b.entries.get(key)
            if val_a != val_b:
                diff[key] = {"old": val_a, "new": val_b}
        return diff

    async def list_changes(self, entry_id: str | None = None) -> list[ConfigChange]:
        if entry_id:
            return [c for c in self._changes if c.entry_id == entry_id]
        return list(self._changes)


__all__ = ["ConfigManager"]
