from __future__ import annotations

import pytest

from eaip.security.key_manager import KeyManager, KeyStatus, RotationSchedule


class TestKeyManager:
    @pytest.fixture
    def manager(self) -> KeyManager:
        return KeyManager()

    def test_create_key(self, manager: KeyManager) -> None:
        key = manager.create_key(
            "k1", algorithm="AES-256", rotation_schedule=RotationSchedule.MONTHLY
        )
        assert key.key_id == "k1"
        assert key.status == KeyStatus.ACTIVE
        assert key.version == 1

    def test_get_key(self, manager: KeyManager) -> None:
        manager.create_key("k1", rotation_schedule=RotationSchedule.WEEKLY)
        key = manager.get_key("k1")
        assert key is not None
        assert key.key_id == "k1"

    def test_get_nonexistent_key(self, manager: KeyManager) -> None:
        key = manager.get_key("nonexistent")
        assert key is None

    def test_list_keys(self, manager: KeyManager) -> None:
        manager.create_key("k1")
        manager.create_key("k2")
        assert len(manager.list_keys()) == 2

    def test_rotate_key(self, manager: KeyManager) -> None:
        manager.create_key("k1")
        result = manager.rotate_key("k1", rotated_by="admin")
        assert result is not None
        assert result.version == 2
        assert result.last_rotated_at is not None

    def test_rotate_nonexistent_key(self, manager: KeyManager) -> None:
        result = manager.rotate_key("nonexistent")
        assert result is None

    def test_revoke_key(self, manager: KeyManager) -> None:
        manager.create_key("k1")
        result = manager.revoke_key("k1", revoked_by="admin")
        assert result is True
        key = manager.get_key("k1")
        assert key is not None
        assert key.status == KeyStatus.REVOKED

    def test_revoke_nonexistent_key(self, manager: KeyManager) -> None:
        result = manager.revoke_key("nonexistent")
        assert result is False

    def test_get_keys_due_for_rotation(self, manager: KeyManager) -> None:
        manager.create_key("k1", rotation_schedule=RotationSchedule.DAILY)
        due = manager.get_keys_due_for_rotation()
        assert len(due) == 1
        assert due[0].key_id == "k1"

    def test_rotate_due_keys(self, manager: KeyManager) -> None:
        manager.create_key("k1")
        rotated = manager.rotate_due_keys()
        assert len(rotated) >= 1

    def test_audit_log(self, manager: KeyManager) -> None:
        manager.create_key("k1")
        manager.rotate_key("k1", rotated_by="admin")
        log = manager.get_audit_log(limit=10)
        assert len(log) >= 2

    def test_audit_log_filtered(self, manager: KeyManager) -> None:
        manager.create_key("k1")
        log = manager.get_audit_log(key_id="k1")
        assert len(log) >= 1
