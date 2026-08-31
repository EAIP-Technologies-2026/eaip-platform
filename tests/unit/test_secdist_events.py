"""Tests for :mod:`eaip.secdist.events`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.secdist.events import (
    DistributionFailed,
    DistributionRevoked,
    SecretDistributed,
)

SecretDistributed.__test__ = False
DistributionFailed.__test__ = False
DistributionRevoked.__test__ = False


class TestSecretsDistributionEvents:
    def test_secret_distributed(self) -> None:
        e = SecretDistributed(package_id="pkg1", target_id="target1", name="api-key")
        assert e.event_type == "eaip.secdist.secret.distributed"
        assert e.package_id == "pkg1"
        assert e.target_id == "target1"
        assert e.name == "api-key"

    def test_distribution_failed(self) -> None:
        e = DistributionFailed(package_id="pkg1", target_id="target1", error_message="timeout")
        assert e.event_type == "eaip.secdist.distribution.failed"
        assert e.error_message == "timeout"

    def test_distribution_revoked(self) -> None:
        e = DistributionRevoked(package_id="pkg1", target_id="target1", reason="key rotation")
        assert e.event_type == "eaip.secdist.distribution.revoked"
        assert e.reason == "key rotation"


class TestEventImmutability:
    def test_secret_distributed_frozen(self) -> None:
        e = SecretDistributed(package_id="pkg1", target_id="target1", name="key")
        with pytest.raises(ValidationError):
            e.package_id = "changed"

    def test_distribution_failed_frozen(self) -> None:
        e = DistributionFailed(package_id="pkg1", target_id="target1", error_message="err")
        with pytest.raises(ValidationError):
            e.target_id = "changed"


class TestEventOccurredAt:
    def test_secret_distributed_has_timestamp(self) -> None:
        e = SecretDistributed(package_id="pkg1", target_id="target1", name="key")
        assert e.occurred_at is not None
