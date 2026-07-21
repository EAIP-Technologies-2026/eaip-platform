"""Key management — automated rotation, key lifecycle, scheduling, audit."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class KeyStatus(StrEnum):
    ACTIVE = "active"
    ROTATING = "rotating"
    ROTATED = "rotated"
    REVOKED = "revoked"
    EXPIRED = "expired"


class RotationSchedule(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    MANUAL = "manual"


class ManagedKey:
    def __init__(
        self,
        key_id: str,
        algorithm: str = "AES-256",
        key_length: int = 256,
        rotation_schedule: RotationSchedule = RotationSchedule.MONTHLY,
    ) -> None:
        self.key_id = key_id
        self.algorithm = algorithm
        self.key_length = key_length
        self.rotation_schedule = rotation_schedule
        self.status = KeyStatus.ACTIVE
        self.created_at = utc_now()
        self.last_rotated_at: datetime | None = None
        self.rotated_by: str | None = None
        self.version: int = 1


class KeyAuditEntry:
    def __init__(self, key_id: str, action: str, actor: str, details: str = "") -> None:
        self.key_id = key_id
        self.action = action
        self.actor = actor
        self.timestamp = utc_now()
        self.details = details


class KeyManager:
    def __init__(self, event_bus: Any = None) -> None:
        self._keys: dict[str, ManagedKey] = {}
        self._audit_log: list[KeyAuditEntry] = []
        self._event_bus = event_bus
        self._log = get_logger("eaip.security.key_manager")

    def create_key(
        self,
        key_id: str,
        algorithm: str = "AES-256",
        key_length: int = 256,
        rotation_schedule: RotationSchedule = RotationSchedule.MONTHLY,
    ) -> ManagedKey:
        key = ManagedKey(
            key_id=key_id,
            algorithm=algorithm,
            key_length=key_length,
            rotation_schedule=rotation_schedule,
        )
        self._keys[key_id] = key
        self._audit(key_id, "key.created", "system")
        return key

    def get_key(self, key_id: str) -> ManagedKey | None:
        return self._keys.get(key_id)

    def list_keys(self) -> list[ManagedKey]:
        return list(self._keys.values())

    def rotate_key(self, key_id: str, rotated_by: str = "system") -> ManagedKey | None:
        key = self._keys.get(key_id)
        if key is None:
            return None
        key.status = KeyStatus.ROTATING
        key.version += 1
        key.last_rotated_at = utc_now()
        key.rotated_by = rotated_by
        key.status = KeyStatus.ACTIVE
        self._audit(key_id, "key.rotated", rotated_by)
        return key

    def revoke_key(self, key_id: str, revoked_by: str = "system") -> bool:
        key = self._keys.get(key_id)
        if key is None:
            return False
        key.status = KeyStatus.REVOKED
        self._audit(key_id, "key.revoked", revoked_by)
        return True

    def get_keys_due_for_rotation(self) -> list[ManagedKey]:
        now = utc_now()
        due: list[ManagedKey] = []
        for key in self._keys.values():
            if key.status != KeyStatus.ACTIVE:
                continue
            if key.last_rotated_at is None:
                due.append(key)
                continue
            delta_days = {
                RotationSchedule.DAILY: 1,
                RotationSchedule.WEEKLY: 7,
                RotationSchedule.MONTHLY: 30,
                RotationSchedule.QUARTERLY: 90,
                RotationSchedule.MANUAL: 10**9,
            }
            max_age = delta_days.get(key.rotation_schedule, 30)
            if (now - key.last_rotated_at) > timedelta(days=max_age):
                due.append(key)
        return due

    def rotate_due_keys(self, rotated_by: str = "system") -> list[ManagedKey]:
        rotated: list[ManagedKey] = []
        for key in self.get_keys_due_for_rotation():
            result = self.rotate_key(key.key_id, rotated_by=rotated_by)
            if result is not None:
                rotated.append(result)
        return rotated

    def get_audit_log(self, key_id: str | None = None, limit: int = 100) -> list[KeyAuditEntry]:
        if key_id:
            return [e for e in self._audit_log if e.key_id == key_id][:limit]
        return self._audit_log[:limit]

    def _audit(self, key_id: str, action: str, actor: str) -> None:
        entry = KeyAuditEntry(key_id=key_id, action=action, actor=actor)
        self._audit_log.append(entry)
        self._log.info("key.audit", key_id=key_id, action=action, actor=actor)


__all__ = [
    "KeyAuditEntry",
    "KeyManager",
    "KeyStatus",
    "ManagedKey",
    "RotationSchedule",
]
