"""Tests for :mod:`eaip.license.enforcement`."""

from __future__ import annotations

import pytest

from eaip.license.enforcement import LicenseEnforcer
from eaip.license.manager import LicenseManager


@pytest.mark.asyncio
class TestLicenseEnforcer:
    async def test_check_feature_access_granted(self) -> None:
        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        lic = await mgr.create_license(
            "Test",
            "key-1",
            features=("feature-a",),
        )
        allowed, reason = await enforcer.check_feature_access(
            lic.id,
            "feature-a",
        )
        assert allowed is True
        assert "granted" in reason.lower()

    async def test_check_feature_access_denied_not_in_features(self) -> None:
        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        lic = await mgr.create_license("Test", "key-1")
        allowed, reason = await enforcer.check_feature_access(
            lic.id,
            "feature-x",
        )
        assert allowed is False
        assert "not entitled" in reason.lower()

    async def test_check_feature_access_denied_revoked(self) -> None:
        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        lic = await mgr.create_license("Test", "key-1", features=("feature-a",))
        await mgr.revoke_license(lic.id)
        allowed, reason = await enforcer.check_feature_access(
            lic.id,
            "feature-a",
        )
        assert allowed is False
        assert "revoked" in reason.lower()

    async def test_check_feature_access_denied_expired(self) -> None:
        from datetime import UTC, datetime, timedelta

        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        past = datetime.now(UTC) - timedelta(days=1)
        lic = await mgr.create_license(
            "Test",
            "key-1",
            features=("feature-a",),
            expires_at=past,
        )
        await mgr.validate_license("key-1")
        allowed, _ = await enforcer.check_feature_access(
            lic.id,
            "feature-a",
        )
        assert allowed is False

    async def test_check_feature_access_license_not_found(self) -> None:
        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        allowed, reason = await enforcer.check_feature_access(
            "nonexistent",
            "feature-a",
        )
        assert allowed is False
        assert "not found" in reason.lower()

    async def test_check_quota_enforcement(self) -> None:
        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        lic = await mgr.create_license("Test", "key-1", max_users=10)
        allowed, current, max_val = await enforcer.check_quota_enforcement(
            lic.id,
            "users",
        )
        assert allowed is True
        assert current == 0
        assert max_val == 10

    async def test_check_quota_enforcement_revoked(self) -> None:
        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        lic = await mgr.create_license("Test", "key-1", max_users=10)
        await mgr.revoke_license(lic.id)
        allowed, _current, _max_val = await enforcer.check_quota_enforcement(
            lic.id,
            "users",
        )
        assert allowed is False

    async def test_get_restrictions_active(self) -> None:
        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        lic = await mgr.create_license(
            "Test",
            "key-1",
            max_users=5,
            max_agents=2,
            features=("a", "b"),
        )
        restrictions = await enforcer.get_restrictions(lic.id)
        assert restrictions["is_active"] is True
        assert restrictions["status"] == "active"
        assert restrictions["max_users"] == 5
        assert restrictions["max_agents"] == 2
        assert "a" in restrictions["features"]

    async def test_get_restrictions_revoked(self) -> None:
        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        lic = await mgr.create_license("Test", "key-1")
        await mgr.revoke_license(lic.id)
        restrictions = await enforcer.get_restrictions(lic.id)
        assert restrictions["is_active"] is False
        assert restrictions["status"] == "revoked"

    async def test_get_restrictions_expired(self) -> None:
        from datetime import UTC, datetime, timedelta

        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        past = datetime.now(UTC) - timedelta(days=1)
        lic = await mgr.create_license(
            "Test",
            "key-1",
            expires_at=past,
        )
        await mgr.validate_license("key-1")
        restrictions = await enforcer.get_restrictions(lic.id)
        assert restrictions["is_expired"] is True

    async def test_get_restrictions_no_expiry(self) -> None:
        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        lic = await mgr.create_license("Test", "key-1")
        restrictions = await enforcer.get_restrictions(lic.id)
        assert restrictions["is_expired"] is False

    async def test_is_license_active_true(self) -> None:
        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        lic = await mgr.create_license("Test", "key-1")
        assert await enforcer.is_license_active(lic.id) is True

    async def test_is_license_active_false(self) -> None:
        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        lic = await mgr.create_license("Test", "key-1")
        await mgr.revoke_license(lic.id)
        assert await enforcer.is_license_active(lic.id) is False

    async def test_is_license_active_not_found(self) -> None:
        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        assert await enforcer.is_license_active("nonexistent") is False

    async def test_check_feature_access_denied_by_entitlement(self) -> None:
        mgr = LicenseManager()
        enforcer = LicenseEnforcer(mgr)
        lic = await mgr.create_license(
            "Test",
            "key-1",
            features=("feature-a",),
        )
        await mgr.create_entitlement(
            lic.id,
            "feature-a",
            enabled=False,
        )
        allowed, reason = await enforcer.check_feature_access(
            lic.id,
            "feature-a",
        )
        assert allowed is False
        assert "disabled" in reason.lower()
