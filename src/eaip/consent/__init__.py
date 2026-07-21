"""Consent & Privacy Management — consent records, privacy preferences, data subject rights."""

from __future__ import annotations

from eaip.consent.events import (
    ConsentRecorded,
    ConsentRevoked,
    ConsentUpdated,
    DataSubjectRequestCompleted,
    PrivacyPreferenceUpdated,
)
from eaip.consent.exceptions import (
    ConsentError,
    ConsentNotFoundError,
    ConsentRevokedError,
    DataSubjectRequestError,
)
from eaip.consent.health import ConsentHealthCheck
from eaip.consent.integration import ConsentRuntimeModule
from eaip.consent.models import (
    ConsentPurpose,
    ConsentRecord,
    ConsentStatus,
    DataSubjectRequest,
    DataSubjectRequestStatus,
    DataSubjectRequestType,
    PrivacyPreference,
)

__all__ = [
    "ConsentError",
    "ConsentHealthCheck",
    "ConsentNotFoundError",
    "ConsentPurpose",
    "ConsentRecord",
    "ConsentRecorded",
    "ConsentRevoked",
    "ConsentRevokedError",
    "ConsentRuntimeModule",
    "ConsentStatus",
    "ConsentUpdated",
    "DataSubjectRequest",
    "DataSubjectRequestCompleted",
    "DataSubjectRequestError",
    "DataSubjectRequestStatus",
    "DataSubjectRequestType",
    "PrivacyPreference",
    "PrivacyPreferenceUpdated",
]
