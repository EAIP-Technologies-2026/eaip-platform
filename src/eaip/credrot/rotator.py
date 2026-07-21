"""Credential rotator — rotate, schedule, manage credentials."""

from __future__ import annotations

from datetime import datetime

from eaip.credrot.exceptions import CredentialNotFoundError
from eaip.credrot.models import Credential, CredRotStatus, RotationSchedule


class CredentialRotator:
    def __init__(self) -> None:
        self._credentials: list[Credential] = []
        self._schedules: list[RotationSchedule] = []

    async def rotate(self, credential_id: str) -> Credential:
        for i, cred in enumerate(self._credentials):
            if cred.id == credential_id:
                updated = cred.model_copy(
                    update={
                        "status": CredRotStatus.ROTATED,
                        "last_rotated_at": datetime.now(),
                    }
                )
                self._credentials[i] = updated
                return updated
        raise CredentialNotFoundError(f"Credential {credential_id} not found")

    async def schedule_rotation(self, schedule: RotationSchedule) -> RotationSchedule:
        self._schedules.append(schedule)
        return schedule

    async def get_credential(self, credential_id: str) -> Credential | None:
        for c in self._credentials:
            if c.id == credential_id:
                return c
        return None

    async def list_credentials(self) -> list[Credential]:
        return list(self._credentials)

    async def list_schedules(self) -> list[RotationSchedule]:
        return list(self._schedules)

    async def create_credential(self, credential: Credential) -> Credential:
        self._credentials.append(credential)
        return credential
