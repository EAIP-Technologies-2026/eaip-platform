"""Tests for :mod:`eaip.license.manager`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from eaip.license.events import (
    LicenseCreated,
    LicenseRevoked,
    LicenseSuspended,
    LicenseValidated,
    QuotaExceeded,
    QuotaWarning,
    UsageRecorded,
)
from eaip.license.exceptions import (
    LicenseExpiredError,
    LicenseNotFoundError,
    QuotaExceededError,
)
from eaip.license.manager import LicenseManager
from eaip.license.models import (
    LicenseConfig,
    LicenseStatus,
    UsageRecord,
)


@pytest.mark.asyncio
class TestLicenseManager:
    async def test_create_license(self) -> None:
        mgr = LicenseManager()
        lic = await mgr.create_license("Test License", "test-key")
        assert lic.name == "Test License"
        assert lic.key == "test-key"
        assert lic.status is LicenseStatus.ACTIVE

    async def test_create_license_emits_event(self) -> None:
        events: list[object] = []
        mgr = LicenseManager(event_callback=events.append)
        await mgr.create_license("Test", "key-1")
        assert len(events) == 1
        assert isinstance(events[0], LicenseCreated)

    async def test_get_license(self) -> None:
        mgr = LicenseManager()
        created = await mgr.create_license("Test", "key-1")
        fetched = await mgr.get_license(created.id)
        assert fetched.id == created.id

    async def test_get_license_not_found(self) -> None:
        mgr = LicenseManager()
        with pytest.raises(LicenseNotFoundError):
            await mgr.get_license("nonexistent")

    async def test_update_license(self) -> None:
        mgr = LicenseManager()
        created = await mgr.create_license("Old", "key-1")
        updated = await mgr.update_license(created.id, name="New")
        assert updated.name == "New"

    async def test_revoke_license(self) -> None:
        events: list[object] = []
        mgr = LicenseManager(event_callback=events.append)
        created = await mgr.create_license("Test", "key-1")
        revoked = await mgr.revoke_license(created.id, reason="Violation")
        assert revoked.status is LicenseStatus.REVOKED
        assert any(isinstance(e, LicenseRevoked) for e in events)

    async def test_suspend_license(self) -> None:
        events: list[object] = []
        mgr = LicenseManager(event_callback=events.append)
        created = await mgr.create_license("Test", "key-1")
        suspended = await mgr.suspend_license(created.id, reason="Non-payment")
        assert suspended.status is LicenseStatus.SUSPENDED
        assert any(isinstance(e, LicenseSuspended) for e in events)

    async def test_list_licenses(self) -> None:
        mgr = LicenseManager()
        await mgr.create_license("A", "key-a")
        await mgr.create_license("B", "key-b")
        assert len(await mgr.list_licenses()) == 2

    async def test_list_licenses_filter_by_status(self) -> None:
        mgr = LicenseManager()
        l1 = await mgr.create_license("A", "key-a")
        await mgr.create_license("B", "key-b")
        await mgr.revoke_license(l1.id)
        active = await mgr.list_licenses(status=LicenseStatus.ACTIVE)
        assert len(active) == 1

    async def test_validate_license_valid(self) -> None:
        mgr = LicenseManager()
        await mgr.create_license("Test", "valid-key")
        result = await mgr.validate_license("valid-key")
        assert result.valid is True
        assert len(result.errors) == 0

    async def test_validate_license_not_found(self) -> None:
        mgr = LicenseManager()
        result = await mgr.validate_license("unknown-key")
        assert result.valid is False
        assert "not found" in result.errors[0].lower()

    async def test_validate_license_expired(self) -> None:
        mgr = LicenseManager()
        past = datetime.now(UTC) - timedelta(days=1)
        await mgr.create_license(
            "Test",
            "expired-key",
            expires_at=past,
        )
        result = await mgr.validate_license("expired-key")
        assert result.valid is False
        assert any("expired" in e.lower() for e in result.errors)

    async def test_validate_license_revoked(self) -> None:
        mgr = LicenseManager()
        created = await mgr.create_license("Test", "revoked-key")
        await mgr.revoke_license(created.id)
        result = await mgr.validate_license("revoked-key")
        assert result.valid is False

    async def test_validate_license_emits_event(self) -> None:
        events: list[object] = []
        mgr = LicenseManager(event_callback=events.append)
        await mgr.create_license("Test", "key-1")
        await mgr.validate_license("key-1")
        assert any(isinstance(e, LicenseValidated) for e in events)

    async def test_validate_license_grace_period_warning(self) -> None:
        config = LicenseConfig(grace_period_days=7)
        mgr = LicenseManager(config=config)
        future = datetime.now(UTC) + timedelta(days=3)
        await mgr.create_license("Test", "grace-key", expires_at=future)
        result = await mgr.validate_license("grace-key")
        assert result.valid is True
        assert len(result.warnings) > 0
        assert "expires" in result.warnings[0].lower()

    async def test_get_entitlement_allowed(self) -> None:
        mgr = LicenseManager()
        lic = await mgr.create_license(
            "Test",
            "key-1",
            features=("feature-a", "feature-b"),
        )
        assert await mgr.get_entitlement(lic.id, "feature-a") is True

    async def test_get_entitlement_denied_when_not_in_features(self) -> None:
        mgr = LicenseManager()
        lic = await mgr.create_license("Test", "key-1")
        assert await mgr.get_entitlement(lic.id, "feature-x") is False

    async def test_get_entitlement_denied_when_revoked(self) -> None:
        mgr = LicenseManager()
        lic = await mgr.create_license("Test", "key-1")
        await mgr.revoke_license(lic.id)
        assert await mgr.get_entitlement(lic.id, "feature-a") is False

    async def test_list_features(self) -> None:
        mgr = LicenseManager()
        lic = await mgr.create_license(
            "Test",
            "key-1",
            features=("a", "b", "c"),
        )
        features = await mgr.list_features(lic.id)
        assert features == ("a", "b", "c")

    async def test_check_quota_allowed(self) -> None:
        mgr = LicenseManager()
        lic = await mgr.create_license("Test", "key-1", max_users=10)
        assert await mgr.check_quota(lic.id, "users", 5) is True

    async def test_check_quota_exceeded(self) -> None:
        mgr = LicenseManager()
        lic = await mgr.create_license("Test", "key-1", max_users=10)
        with pytest.raises(QuotaExceededError):
            await mgr.check_quota(lic.id, "users", 15)

    async def test_check_quota_emits_exceeded_event(self) -> None:
        events: list[object] = []
        mgr = LicenseManager(event_callback=events.append)
        lic = await mgr.create_license("Test", "key-1", max_users=5)
        with pytest.raises(QuotaExceededError):
            await mgr.check_quota(lic.id, "users", 10)
        assert any(isinstance(e, QuotaExceeded) for e in events)

    async def test_check_quota_emits_warning(self) -> None:
        events: list[object] = []
        mgr = LicenseManager(event_callback=events.append)
        lic = await mgr.create_license("Test", "key-1", max_users=10)
        await mgr.check_quota(lic.id, "users", 8)
        assert any(isinstance(e, QuotaWarning) for e in events)

    async def test_record_usage(self) -> None:
        mgr = LicenseManager()
        lic = await mgr.create_license("Test", "key-1")
        rec = await mgr.record_usage(lic.id, "feature-a", "api_calls", 5)
        assert isinstance(rec, UsageRecord)
        assert rec.quantity == 5
        assert rec.feature_key == "feature-a"

    async def test_record_usage_emits_event(self) -> None:
        events: list[object] = []
        mgr = LicenseManager(event_callback=events.append)
        lic = await mgr.create_license("Test", "key-1")
        await mgr.record_usage(lic.id, "feature-a", "api_calls", 1)
        assert any(isinstance(e, UsageRecorded) for e in events)

    async def test_record_usage_fails_on_expired(self) -> None:
        mgr = LicenseManager()
        past = datetime.now(UTC) - timedelta(days=1)
        lic = await mgr.create_license(
            "Test",
            "key-1",
            expires_at=past,
        )
        await mgr.validate_license("key-1")
        with pytest.raises(LicenseExpiredError):
            await mgr.record_usage(lic.id, "feature-a", "api_calls")

    async def test_create_entitlement(self) -> None:
        mgr = LicenseManager()
        lic = await mgr.create_license("Test", "key-1")
        ent = await mgr.create_entitlement(
            lic.id,
            "feature-a",
            enabled=True,
            limits={"max_calls": 500},
        )
        assert ent.license_id == lic.id
        assert ent.feature_key == "feature-a"
        assert ent.enabled is True

    async def test_get_entitlements(self) -> None:
        mgr = LicenseManager()
        lic = await mgr.create_license("Test", "key-1")
        await mgr.create_entitlement(lic.id, "feature-a")
        await mgr.create_entitlement(lic.id, "feature-b")
        ents = await mgr.get_entitlements(lic.id)
        assert len(ents) == 2

    async def test_set_event_callback(self) -> None:
        events: list[object] = []
        mgr = LicenseManager()
        mgr.set_event_callback(events.append)
        await mgr.create_license("Test", "key-1")
        assert len(events) == 1

    async def test_usage_records_empty(self) -> None:
        mgr = LicenseManager()
        lic = await mgr.create_license("Test", "key-1")
        records = await mgr.get_usage_records(lic.id)
        assert records == []

    async def test_usage_records_with_data(self) -> None:
        mgr = LicenseManager()
        lic = await mgr.create_license("Test", "key-1")
        await mgr.record_usage(lic.id, "fa", "calls", 1)
        await mgr.record_usage(lic.id, "fa", "calls", 2)
        records = await mgr.get_usage_records(lic.id)
        assert len(records) == 2

    async def test_validate_license_updates_last_validated_at(self) -> None:
        mgr = LicenseManager()
        lic = await mgr.create_license("Test", "key-1")
        await mgr.validate_license("key-1")
        fetched = await mgr.get_license(lic.id)
        assert fetched.last_validated_at is not None

    async def test_record_usage_disabled(self) -> None:
        config = LicenseConfig(enable_usage_tracking=False)
        mgr = LicenseManager(config=config)
        lic = await mgr.create_license("Test", "key-1")
        with pytest.raises(RuntimeError, match="disabled"):
            await mgr.record_usage(lic.id, "fa", "calls")

    async def test_validate_expired_license_auto_status_change(self) -> None:
        mgr = LicenseManager()
        past = datetime.now(UTC) - timedelta(days=1)
        lic = await mgr.create_license(
            "Test",
            "key-1",
            expires_at=past,
        )
        await mgr.validate_license("key-1")
        fetched = await mgr.get_license(lic.id)
        assert fetched.status is LicenseStatus.EXPIRED
