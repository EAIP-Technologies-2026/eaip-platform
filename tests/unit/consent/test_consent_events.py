from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.consent.events import (
    ConsentRecorded,
    ConsentRevoked,
    ConsentUpdated,
    DataSubjectRequestCompleted,
    PrivacyPreferenceUpdated,
)


class TestConsentEvents:
    def test_consent_recorded(self) -> None:
        event = ConsentRecorded(consent_id="c1", subject_id="u1", purpose="data_processing")
        assert event.event_type == "consent.recorded"

    def test_consent_updated(self) -> None:
        event = ConsentUpdated(consent_id="c1", subject_id="u1", new_status="revoked")
        assert event.event_type == "consent.updated"

    def test_consent_revoked(self) -> None:
        event = ConsentRevoked(consent_id="c1", subject_id="u1", purpose="marketing")
        assert event.event_type == "consent.revoked"

    def test_privacy_preference_updated(self) -> None:
        event = PrivacyPreferenceUpdated(subject_id="u1")
        assert event.event_type == "privacy.preference.updated"

    def test_data_subject_request_completed(self) -> None:
        event = DataSubjectRequestCompleted(
            request_id="r1", subject_id="u1", request_type="access", status="completed"
        )
        assert event.event_type == "datasubject.request.completed"

    def test_events_are_frozen(self) -> None:
        event = ConsentRecorded(consent_id="c1", subject_id="u1", purpose="data_processing")
        with pytest.raises((TypeError, ValidationError)):
            event.consent_id = "c2"  # type: ignore[misc]
