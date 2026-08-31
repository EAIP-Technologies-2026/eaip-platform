"""Tests for :mod:`eaip.license.models`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.license.models import (
    FeatureEntitlement,
    License,
    LicenseConfig,
    LicenseStatus,
    LicenseType,
    LicenseValidationResult,
    UsageRecord,
)


class TestLicenseType:
    def test_values(self) -> None:
        assert LicenseType.TRIAL.value == "trial"
        assert LicenseType.SUBSCRIPTION.value == "subscription"
        assert LicenseType.PERPETUAL.value == "perpetual"
        assert LicenseType.USAGE_BASED.value == "usage_based"


class TestLicenseStatus:
    def test_values(self) -> None:
        assert LicenseStatus.ACTIVE.value == "active"
        assert LicenseStatus.EXPIRED.value == "expired"
        assert LicenseStatus.SUSPENDED.value == "suspended"
        assert LicenseStatus.REVOKED.value == "revoked"


class TestLicense:
    def test_create_minimal(self) -> None:
        lic = License(id="l1", name="Test License", key="test-key")
        assert lic.id == "l1"
        assert lic.type is LicenseType.TRIAL
        assert lic.status is LicenseStatus.ACTIVE
        assert lic.features == ()
        assert lic.max_users == 0
        assert lic.metadata == {}

    def test_create_full(self) -> None:
        now = datetime.now(UTC)
        lic = License(
            id="l2",
            name="Full License",
            key="full-key",
            type=LicenseType.SUBSCRIPTION,
            status=LicenseStatus.ACTIVE,
            features=("feature-a", "feature-b"),
            max_users=10,
            max_agents=5,
            max_workflows=20,
            max_storage_bytes=1073741824,
            issued_at=now,
            expires_at=now,
            metadata={"region": "us-east"},
            customer_info={"name": "Acme Corp"},
        )
        assert lic.type is LicenseType.SUBSCRIPTION
        assert len(lic.features) == 2
        assert lic.max_users == 10
        assert lic.max_agents == 5
        assert lic.max_workflows == 20
        assert lic.max_storage_bytes == 1073741824

    def test_frozen(self) -> None:
        lic = License(id="l1", name="Test", key="k")
        with pytest.raises(ValidationError):
            lic.name = "Changed"

    def test_default_timestamps(self) -> None:
        lic = License(id="l1", name="Test", key="k")
        assert lic.issued_at is not None

    def test_expires_at_optional(self) -> None:
        lic = License(id="l1", name="Test", key="k")
        assert lic.expires_at is None


class TestFeatureEntitlement:
    def test_create_minimal(self) -> None:
        ent = FeatureEntitlement(
            id="e1",
            license_id="l1",
            feature_key="feature-a",
        )
        assert ent.enabled is True
        assert ent.limits == {}

    def test_create_full(self) -> None:
        ent = FeatureEntitlement(
            id="e2",
            license_id="l1",
            feature_key="feature-b",
            enabled=False,
            limits={"max_calls": 1000},
            metadata={"tier": "premium"},
        )
        assert ent.enabled is False
        assert ent.limits["max_calls"] == 1000

    def test_frozen(self) -> None:
        ent = FeatureEntitlement(id="e1", license_id="l1", feature_key="fk")
        with pytest.raises(ValidationError):
            ent.enabled = False


class TestUsageRecord:
    def test_create_minimal(self) -> None:
        rec = UsageRecord(
            id="r1",
            license_id="l1",
            feature_key="fk",
            metric="api_calls",
        )
        assert rec.quantity == 1
        assert rec.timestamp is not None

    def test_create_full(self) -> None:
        now = datetime.now(UTC)
        rec = UsageRecord(
            id="r2",
            license_id="l1",
            feature_key="fk",
            metric="tokens",
            quantity=500,
            timestamp=now,
            metadata={"source": "batch"},
        )
        assert rec.quantity == 500
        assert rec.metadata["source"] == "batch"

    def test_quantity_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            UsageRecord(
                id="r1",
                license_id="l1",
                feature_key="fk",
                metric="api_calls",
                quantity=0,
            )

    def test_frozen(self) -> None:
        rec = UsageRecord(id="r1", license_id="l1", feature_key="fk", metric="m")
        with pytest.raises(ValidationError):
            rec.quantity = 10


class TestLicenseValidationResult:
    def test_create_minimal_valid(self) -> None:
        result = LicenseValidationResult(
            id="vr1",
            license_id="l1",
            valid=True,
        )
        assert result.valid is True
        assert result.errors == ()

    def test_create_with_errors(self) -> None:
        result = LicenseValidationResult(
            id="vr2",
            license_id="l1",
            valid=False,
            errors=("License expired",),
            warnings=("Renewal due",),
            features_available=(),
            features_blocked=("feature-a",),
            expires_in_days=0,
        )
        assert len(result.errors) == 1
        assert "feature-a" in result.features_blocked

    def test_frozen(self) -> None:
        result = LicenseValidationResult(id="vr1", license_id="l1", valid=True)
        with pytest.raises(ValidationError):
            result.valid = False


class TestLicenseConfig:
    def test_defaults(self) -> None:
        c = LicenseConfig()
        assert c.enable_offline_validation is True
        assert c.validation_interval_hours == 24
        assert c.grace_period_days == 7
        assert c.enable_usage_tracking is True
        assert c.enable_enforcement is True
        assert c.default_license_type is LicenseType.TRIAL

    def test_custom(self) -> None:
        c = LicenseConfig(
            enable_offline_validation=False,
            validation_interval_hours=12,
            grace_period_days=3,
            enable_usage_tracking=False,
            enable_enforcement=False,
            default_license_type=LicenseType.SUBSCRIPTION,
        )
        assert c.enable_offline_validation is False
        assert c.validation_interval_hours == 12
        assert c.grace_period_days == 3
        assert c.enable_usage_tracking is False
        assert c.enable_enforcement is False
        assert c.default_license_type is LicenseType.SUBSCRIPTION

    def test_frozen(self) -> None:
        c = LicenseConfig()
        with pytest.raises(ValidationError):
            c.enable_offline_validation = False


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        License(id="l1", name="Test", key="k", unknown_field="value")
