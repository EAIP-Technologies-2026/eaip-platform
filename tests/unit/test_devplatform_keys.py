"""Tests for :mod:`eaip.devplatform.developer_keys`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from eaip.devplatform.developer_keys import DeveloperKeyManager
from eaip.devplatform.events import DeveloperKeyCreated, DeveloperKeyRevoked
from eaip.devplatform.exceptions import KeyExpiredError, KeyNotFoundError


@pytest.fixture
def manager() -> DeveloperKeyManager:
    return DeveloperKeyManager()


class TestDeveloperKeyManager:
    async def test_create_key(self, manager: DeveloperKeyManager) -> None:
        key, raw = await manager.create_key("d1", "My Key")
        assert key.name == "My Key"
        assert key.developer_id == "d1"
        assert key.enabled is True
        assert len(raw) > 0
        assert key.key_prefix == raw[:8]

    async def test_create_key_emits_event(self, manager: DeveloperKeyManager) -> None:
        events: list[DeveloperKeyCreated] = []
        manager.on_event(events.append)
        await manager.create_key("d1", "Test Key")
        assert len(events) == 1
        assert events[0].developer_id == "d1"

    async def test_create_key_with_permissions(self, manager: DeveloperKeyManager) -> None:
        key, _raw = await manager.create_key("d1", "Admin", permissions=("read", "write"))
        assert "read" in key.permissions

    async def test_create_key_with_expiry(self, manager: DeveloperKeyManager) -> None:
        future = datetime.now(UTC) + timedelta(days=30)
        key, _raw = await manager.create_key("d1", "Temp", expires_at=future)
        assert key.expires_at is not None

    async def test_get_key(self, manager: DeveloperKeyManager) -> None:
        key, _raw = await manager.create_key("d1", "My Key")
        retrieved = await manager.get_key(key.id)
        assert retrieved.id == key.id
        assert retrieved.name == "My Key"

    async def test_get_key_not_found(self, manager: DeveloperKeyManager) -> None:
        with pytest.raises(KeyNotFoundError):
            await manager.get_key("nonexistent")

    async def test_revoke_key(self, manager: DeveloperKeyManager) -> None:
        key, _raw = await manager.create_key("d1", "To Revoke")
        revoked = await manager.revoke_key(key.id)
        assert revoked.enabled is False

    async def test_revoke_key_emits_event(self, manager: DeveloperKeyManager) -> None:
        key, _raw = await manager.create_key("d1", "To Revoke")
        events: list[DeveloperKeyRevoked] = []
        manager.on_event(events.append)
        await manager.revoke_key(key.id)
        assert len(events) == 1
        assert events[0].key_id == key.id

    async def test_revoke_key_not_found(self, manager: DeveloperKeyManager) -> None:
        with pytest.raises(KeyNotFoundError):
            await manager.revoke_key("nonexistent")

    async def test_validate_key_valid(self, manager: DeveloperKeyManager) -> None:
        key, raw = await manager.create_key("d1", "Valid Key")
        validated = await manager.validate_key(raw)
        assert validated.id == key.id

    async def test_validate_key_revoked(self, manager: DeveloperKeyManager) -> None:
        key, raw = await manager.create_key("d1", "Revoked Key")
        await manager.revoke_key(key.id)
        with pytest.raises(KeyExpiredError):
            await manager.validate_key(raw)

    async def test_validate_key_expired(self, manager: DeveloperKeyManager) -> None:
        past = datetime.now(UTC) - timedelta(days=1)
        _key, raw = await manager.create_key("d1", "Expired Key", expires_at=past)
        with pytest.raises(KeyExpiredError):
            await manager.validate_key(raw)

    async def test_validate_key_not_found(self, manager: DeveloperKeyManager) -> None:
        with pytest.raises(KeyNotFoundError):
            await manager.validate_key("badbadbaddeadbeef")

    async def test_list_keys_all(self, manager: DeveloperKeyManager) -> None:
        await manager.create_key("d1", "Key 1")
        await manager.create_key("d2", "Key 2")
        keys = await manager.list_keys()
        assert len(keys) == 2

    async def test_list_keys_by_developer(self, manager: DeveloperKeyManager) -> None:
        await manager.create_key("d1", "Key 1")
        await manager.create_key("d1", "Key 2")
        await manager.create_key("d2", "Key 3")
        keys = await manager.list_keys("d1")
        assert len(keys) == 2

    async def test_record_key_usage(self, manager: DeveloperKeyManager) -> None:
        key, _raw = await manager.create_key("d1", "Used Key")
        updated = await manager.record_key_usage(key.id)
        assert updated.last_used_at is not None

    async def test_record_key_usage_not_found(self, manager: DeveloperKeyManager) -> None:
        with pytest.raises(KeyNotFoundError):
            await manager.record_key_usage("nonexistent")

    async def test_check_rate_limit(self, manager: DeveloperKeyManager) -> None:
        key, _raw = await manager.create_key("d1", "Limited Key")
        result = await manager.check_rate_limit(key.id)
        assert result is True

    async def test_check_rate_limit_not_found(self, manager: DeveloperKeyManager) -> None:
        with pytest.raises(KeyNotFoundError):
            await manager.check_rate_limit("nonexistent")
