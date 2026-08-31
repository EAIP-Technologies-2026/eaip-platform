from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.consent.models import (
    ConsentPurpose,
    ConsentRecord,
    ConsentStatus,
    DataSubjectRequest,
    DataSubjectRequestStatus,
    DataSubjectRequestType,
    PrivacyPreference,
)


class TestConsentModels:
    def test_consent_record_defaults(self) -> None:
        r = ConsentRecord(id="c1", subject_id="u1", purpose=ConsentPurpose.DATA_PROCESSING)
        assert r.status == ConsentStatus.ACTIVE
        assert r.revoked_at is None

    def test_consent_record_frozen(self) -> None:
        r = ConsentRecord(id="c1", subject_id="u1", purpose=ConsentPurpose.DATA_PROCESSING)
        with pytest.raises((TypeError, ValidationError)):
            r.status = ConsentStatus.REVOKED  # type: ignore[misc]

    def test_privacy_preference_defaults(self) -> None:
        p = PrivacyPreference(subject_id="u1")
        assert p.opt_out_marketing is False
        assert p.data_retention_days == 365

    def test_data_subject_request_defaults(self) -> None:
        r = DataSubjectRequest(id="r1", subject_id="u1", request_type=DataSubjectRequestType.ACCESS)
        assert r.status == DataSubjectRequestStatus.PENDING
        assert r.response_data == {}

    def test_consent_purpose_enum(self) -> None:
        assert ConsentPurpose.MARKETING.value == "marketing"
        assert ConsentPurpose.RESEARCH.value == "research"

    def test_consent_status_enum(self) -> None:
        assert ConsentStatus.EXPIRED.value == "expired"

    def test_request_type_enum(self) -> None:
        assert DataSubjectRequestType.PORTABILITY.value == "portability"

    def test_request_status_enum(self) -> None:
        assert DataSubjectRequestStatus.APPROVED.value == "approved"
