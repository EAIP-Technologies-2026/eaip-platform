"""EP-0142 — Credential Rotator — automated secret rotation lifecycle."""

from __future__ import annotations

from eaip.credrot.events import (
    CredentialRotated,
    RotationFailed,
    RotationScheduled,
)
from eaip.credrot.exceptions import (
    CredentialNotFoundError,
    CredRotError,
)
from eaip.credrot.health import CredRotHealthCheck
from eaip.credrot.integration import CredRotRuntimeModule
from eaip.credrot.models import (
    Credential,
    CredRotConfig,
    CredRotStatus,
    RotationSchedule,
)
from eaip.credrot.rotator import CredentialRotator

__all__ = [
    "CredRotConfig",
    "CredRotError",
    "CredRotHealthCheck",
    "CredRotRuntimeModule",
    "CredRotStatus",
    "Credential",
    "CredentialNotFoundError",
    "CredentialRotated",
    "CredentialRotator",
    "RotationFailed",
    "RotationSchedule",
    "RotationScheduled",
]
