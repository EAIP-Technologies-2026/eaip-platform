from __future__ import annotations

from eaip.consent.exceptions import (
    ConsentError,
    ConsentNotFoundError,
    ConsentRevokedError,
    DataSubjectRequestError,
)
from eaip.exceptions.base import EAIPError, ErrorCode


class TestConsentExceptions:
    def test_consent_error_is_eaiperror(self) -> None:
        assert issubclass(ConsentError, EAIPError)

    def test_consent_not_found_error(self) -> None:
        err = ConsentNotFoundError("not found")
        assert "not found" in str(err)
        assert err.default_code == ErrorCode.NOT_FOUND

    def test_consent_revoked_error(self) -> None:
        err = ConsentRevokedError("already revoked")
        assert "already revoked" in str(err)

    def test_data_subject_request_error(self) -> None:
        err = DataSubjectRequestError("request failed")
        assert "request failed" in str(err)
