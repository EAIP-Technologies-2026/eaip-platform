"""Tests for :mod:`eaip.license.events`."""

from __future__ import annotations

import pytest

from eaip.license.events import (
    FeatureAccessDenied,
    FeatureAccessGranted,
    LicenseActivated,
    LicenseCreated,
    LicenseExpired,
    LicenseRevoked,
    LicenseSuspended,
    LicenseValidated,
    QuotaExceeded,
    QuotaWarning,
    UsageRecorded,
)


class TestLicenseCreated:
    def test_minimal(self) -> None:
        e = LicenseCreated(
            license_id="l1",
            name="Test",
            key="test-key",
            license_type="trial",
        )
        assert e.event_type == "eaip.license.created"
        assert e.license_id == "l1"

    def test_with_features(self) -> None:
        e = LicenseCreated(
            license_id="l1",
            name="Test",
            key="test-key",
            license_type="subscription",
            features=("feature-a", "feature-b"),
        )
        assert len(e.features) == 2

    def test_frozen(self) -> None:
        e = LicenseCreated(
            license_id="l1",
            name="n",
            key="k",
            license_type="trial",
        )
        with pytest.raises(ValueError):
            e.license_id = "l2"


class TestLicenseActivated:
    def test_create(self) -> None:
        e = LicenseActivated(license_id="l1", key="test-key")
        assert e.event_type == "eaip.license.activated"


class TestLicenseExpired:
    def test_create(self) -> None:
        e = LicenseExpired(
            license_id="l1",
            key="test-key",
            expired_at="2026-01-01T00:00:00",
        )
        assert e.event_type == "eaip.license.expired"
        assert e.expired_at == "2026-01-01T00:00:00"


class TestLicenseRevoked:
    def test_minimal(self) -> None:
        e = LicenseRevoked(license_id="l1", key="test-key")
        assert e.event_type == "eaip.license.revoked"
        assert e.reason == ""

    def test_with_reason(self) -> None:
        e = LicenseRevoked(
            license_id="l1",
            key="test-key",
            reason="Terms violation",
        )
        assert e.reason == "Terms violation"


class TestLicenseSuspended:
    def test_minimal(self) -> None:
        e = LicenseSuspended(license_id="l1", key="test-key")
        assert e.event_type == "eaip.license.suspended"

    def test_with_reason(self) -> None:
        e = LicenseSuspended(
            license_id="l1",
            key="test-key",
            reason="Non-payment",
        )
        assert e.reason == "Non-payment"


class TestLicenseValidated:
    def test_valid(self) -> None:
        e = LicenseValidated(
            license_id="l1",
            key="test-key",
            valid=True,
        )
        assert e.event_type == "eaip.license.validated"
        assert e.valid is True

    def test_with_errors(self) -> None:
        e = LicenseValidated(
            license_id="l1",
            key="test-key",
            valid=False,
            errors=("License expired",),
            warnings=("Renewal due",),
        )
        assert len(e.errors) == 1
        assert len(e.warnings) == 1


class TestFeatureAccessGranted:
    def test_create(self) -> None:
        e = FeatureAccessGranted(
            license_id="l1",
            feature_key="feature-a",
        )
        assert e.event_type == "eaip.license.feature.granted"


class TestFeatureAccessDenied:
    def test_minimal(self) -> None:
        e = FeatureAccessDenied(
            license_id="l1",
            feature_key="feature-a",
        )
        assert e.event_type == "eaip.license.feature.denied"

    def test_with_reason(self) -> None:
        e = FeatureAccessDenied(
            license_id="l1",
            feature_key="feature-a",
            reason="Not entitled",
        )
        assert e.reason == "Not entitled"


class TestUsageRecorded:
    def test_create(self) -> None:
        e = UsageRecorded(
            license_id="l1",
            feature_key="feature-a",
            metric="api_calls",
            quantity=5,
        )
        assert e.event_type == "eaip.license.usage.recorded"
        assert e.quantity == 5

    def test_frozen(self) -> None:
        e = UsageRecorded(
            license_id="l1",
            feature_key="fa",
            metric="m",
            quantity=1,
        )
        with pytest.raises(ValueError):
            e.quantity = 10


class TestQuotaWarning:
    def test_create(self) -> None:
        e = QuotaWarning(
            license_id="l1",
            resource_type="users",
            current=8,
            max=10,
            usage_percent=80.0,
        )
        assert e.event_type == "eaip.license.quota.warning"
        assert e.usage_percent == 80.0


class TestQuotaExceeded:
    def test_create(self) -> None:
        e = QuotaExceeded(
            license_id="l1",
            resource_type="users",
            current=10,
            max=10,
            requested=5,
        )
        assert e.event_type == "eaip.license.quota.exceeded"
        assert e.requested == 5


def test_all_events_have_unique_types() -> None:
    types = [
        LicenseCreated(license_id="l1", name="n", key="k", license_type="t").event_type,
        LicenseActivated(license_id="l1", key="k").event_type,
        LicenseExpired(license_id="l1", key="k", expired_at="2026-01-01").event_type,
        LicenseRevoked(license_id="l1", key="k").event_type,
        LicenseSuspended(license_id="l1", key="k").event_type,
        LicenseValidated(license_id="l1", key="k", valid=True).event_type,
        FeatureAccessGranted(license_id="l1", feature_key="fk").event_type,
        FeatureAccessDenied(license_id="l1", feature_key="fk").event_type,
        UsageRecorded(license_id="l1", feature_key="fk", metric="m", quantity=1).event_type,
        QuotaWarning(
            license_id="l1", resource_type="u", current=1, max=10, usage_percent=10.0
        ).event_type,
        QuotaExceeded(
            license_id="l1", resource_type="u", current=10, max=10, requested=1
        ).event_type,
    ]
    assert len(types) == len(set(types)), "event types must be unique"
