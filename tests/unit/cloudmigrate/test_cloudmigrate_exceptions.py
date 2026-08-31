"""Tests for cloud migration exception hierarchy."""

from __future__ import annotations

from eaip.cloudmigrate.exceptions import (
    AssessmentNotFoundError,
    MigrationError,
    PlanNotFoundError,
)
from eaip.exceptions.base import EAIPError, ErrorCode


class TestMigrationError:
    def test_is_eaip_error(self) -> None:
        err = MigrationError("generic error")
        assert isinstance(err, EAIPError)

    def test_default_code(self) -> None:
        err = MigrationError("test")
        assert err.code == ErrorCode.UNKNOWN


class TestAssessmentNotFoundError:
    def test_inherits_migration_error(self) -> None:
        err = AssessmentNotFoundError("not found")
        assert isinstance(err, MigrationError)

    def test_default_code(self) -> None:
        err = AssessmentNotFoundError("missing")
        assert err.code == ErrorCode.NOT_FOUND


class TestPlanNotFoundError:
    def test_inherits_migration_error(self) -> None:
        err = PlanNotFoundError("not found")
        assert isinstance(err, MigrationError)

    def test_default_code(self) -> None:
        err = PlanNotFoundError("missing")
        assert err.code == ErrorCode.NOT_FOUND
