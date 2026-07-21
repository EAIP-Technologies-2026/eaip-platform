"""Tests for deploy exception hierarchy."""

from __future__ import annotations

from eaip.deploy.exceptions import (
    DeployError,
    DeploymentFailedError,
    InvalidEnvironmentError,
    ReleaseNotFoundError,
    RollbackFailedError,
)
from eaip.exceptions.base import EAIPError, ErrorCode


class TestDeployError:
    def test_base_inheritance(self) -> None:
        err = DeployError("generic deploy error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.UNKNOWN

    def test_default_code(self) -> None:
        assert DeployError.default_code == ErrorCode.UNKNOWN


class TestReleaseNotFoundError:
    def test_message(self) -> None:
        err = ReleaseNotFoundError("r-123")
        assert "r-123" in str(err)
        assert err.release_id == "r-123"

    def test_code(self) -> None:
        err = ReleaseNotFoundError("r-123")
        assert err.code == ErrorCode.NOT_FOUND

    def test_default_code(self) -> None:
        assert ReleaseNotFoundError.default_code == ErrorCode.NOT_FOUND


class TestDeploymentFailedError:
    def test_message(self) -> None:
        err = DeploymentFailedError("d-456", "timeout exceeded")
        assert "d-456" in str(err)
        assert "timeout" in str(err)
        assert err.deployment_id == "d-456"

    def test_code(self) -> None:
        err = DeploymentFailedError("d-456", "timeout")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_default_code(self) -> None:
        assert DeploymentFailedError.default_code == ErrorCode.INTERNAL_ERROR


class TestRollbackFailedError:
    def test_message(self) -> None:
        err = RollbackFailedError("d-789", "no previous version")
        assert "d-789" in str(err)
        assert err.deployment_id == "d-789"

    def test_code(self) -> None:
        err = RollbackFailedError("d-789", "no previous version")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_default_code(self) -> None:
        assert RollbackFailedError.default_code == ErrorCode.INTERNAL_ERROR


class TestInvalidEnvironmentError:
    def test_message(self) -> None:
        err = InvalidEnvironmentError("invalid-env")
        assert "invalid-env" in str(err)
        assert err.environment == "invalid-env"

    def test_code(self) -> None:
        err = InvalidEnvironmentError("invalid-env")
        assert err.code == ErrorCode.VALIDATION_FAILED

    def test_default_code(self) -> None:
        assert InvalidEnvironmentError.default_code == ErrorCode.VALIDATION_FAILED
