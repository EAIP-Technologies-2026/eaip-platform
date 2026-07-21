"""Tests for :mod:`eaip.credrot.models`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.credrot.models import CredRotConfig, CredRotStatus, Credential, RotationSchedule


class TestCredential:
    def test_create_minimal(self) -> None:
        c = Credential(id="c1", name="MySecret", type="api_key")
        assert c.id == "c1"
        assert c.name == "MySecret"
        assert c.type == "api_key"
        assert c.status is CredRotStatus.ACTIVE
        assert c.rotation_frequency_days == 90

    def test_create_rotating(self) -> None:
        c = Credential(id="c2", name="MySecret", type="api_key", status=CredRotStatus.ROTATING)
        assert c.status is CredRotStatus.ROTATING

    def test_frozen(self) -> None:
        c = Credential(id="c3", name="MySecret", type="api_key")
        with pytest.raises(ValidationError):
            c.name = "NewName"

    def test_status_enum_values(self) -> None:
        assert CredRotStatus.ACTIVE.value == "active"
        assert CredRotStatus.ROTATING.value == "rotating"
        assert CredRotStatus.ROTATED.value == "rotated"
        assert CredRotStatus.REVOKED.value == "revoked"


class TestRotationSchedule:
    def test_create(self) -> None:
        now = datetime.now(UTC)
        s = RotationSchedule(id="s1", credential_id="c1", scheduled_at=now)
        assert s.credential_id == "c1"
        assert s.status is CredRotStatus.ACTIVE

    def test_frozen(self) -> None:
        now = datetime.now(UTC)
        s = RotationSchedule(id="s2", credential_id="c1", scheduled_at=now)
        with pytest.raises(ValidationError):
            s.status = CredRotStatus.ROTATED


class TestCredRotConfig:
    def test_defaults(self) -> None:
        c = CredRotConfig()
        assert c.default_frequency_days == 90
        assert c.auto_rotate is True
        assert c.notify_before_days == 7
        assert c.max_rotation_retries == 3

    def test_custom(self) -> None:
        c = CredRotConfig(default_frequency_days=30, auto_rotate=False, max_rotation_retries=5)
        assert c.default_frequency_days == 30
        assert c.auto_rotate is False

    def test_frozen(self) -> None:
        c = CredRotConfig()
        with pytest.raises(ValidationError):
            c.default_frequency_days = 60


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        Credential(id="x", name="t", type="k", unknown="field")
