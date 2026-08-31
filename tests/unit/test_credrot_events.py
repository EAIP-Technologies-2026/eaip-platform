"""Tests for :mod:`eaip.credrot.events`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.credrot.events import CredentialRotated, RotationFailed, RotationScheduled


class TestCredentialRotated:
    def test_create(self) -> None:
        now = datetime.now(UTC)
        e = CredentialRotated(credential_id="c1", name="MySecret", type="api_key", rotated_at=now)
        assert e.event_type == "eaip.credrot.rotated"
        assert e.credential_id == "c1"

    def test_frozen(self) -> None:
        now = datetime.now(UTC)
        e = CredentialRotated(credential_id="c1", name="MySecret", type="api_key", rotated_at=now)
        with pytest.raises(ValueError):
            e.name = "NewName"


class TestRotationScheduled:
    def test_create(self) -> None:
        now = datetime.now(UTC)
        e = RotationScheduled(schedule_id="s1", credential_id="c1", scheduled_at=now)
        assert e.event_type == "eaip.credrot.scheduled"


class TestRotationFailed:
    def test_create(self) -> None:
        e = RotationFailed(credential_id="c1", name="MySecret", error="Timeout")
        assert e.event_type == "eaip.credrot.failed"
        assert e.error == "Timeout"
