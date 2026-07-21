"""Tests for :mod:`eaip.credrot.rotator`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.credrot.exceptions import CredentialNotFoundError
from eaip.credrot.models import CredRotStatus, Credential, RotationSchedule
from eaip.credrot.rotator import CredentialRotator


@pytest.fixture
def rotator() -> CredentialRotator:
    return CredentialRotator()


class TestCredentialRotator:
    @pytest.mark.asyncio
    async def test_create_credential(self, rotator: CredentialRotator) -> None:
        c = Credential(id="c1", name="MySecret", type="api_key")
        result = await rotator.create_credential(c)
        assert result.id == "c1"

    @pytest.mark.asyncio
    async def test_list_credentials_empty(self, rotator: CredentialRotator) -> None:
        assert await rotator.list_credentials() == []

    @pytest.mark.asyncio
    async def test_get_credential_found(self, rotator: CredentialRotator) -> None:
        c = Credential(id="c1", name="MySecret", type="api_key")
        await rotator.create_credential(c)
        found = await rotator.get_credential("c1")
        assert found is not None
        assert found.name == "MySecret"

    @pytest.mark.asyncio
    async def test_get_credential_not_found(self, rotator: CredentialRotator) -> None:
        found = await rotator.get_credential("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_rotate(self, rotator: CredentialRotator) -> None:
        c = Credential(id="c1", name="MySecret", type="api_key")
        await rotator.create_credential(c)
        rotated = await rotator.rotate("c1")
        assert rotated.status is CredRotStatus.ROTATED
        assert rotated.last_rotated_at is not None

    @pytest.mark.asyncio
    async def test_rotate_not_found(self, rotator: CredentialRotator) -> None:
        with pytest.raises(CredentialNotFoundError):
            await rotator.rotate("nonexistent")

    @pytest.mark.asyncio
    async def test_schedule_rotation(self, rotator: CredentialRotator) -> None:
        now = datetime.now(UTC)
        s = RotationSchedule(id="s1", credential_id="c1", scheduled_at=now)
        result = await rotator.schedule_rotation(s)
        assert result.id == "s1"

    @pytest.mark.asyncio
    async def test_list_schedules(self, rotator: CredentialRotator) -> None:
        now = datetime.now(UTC)
        s = RotationSchedule(id="s1", credential_id="c1", scheduled_at=now)
        await rotator.schedule_rotation(s)
        schedules = await rotator.list_schedules()
        assert len(schedules) == 1
