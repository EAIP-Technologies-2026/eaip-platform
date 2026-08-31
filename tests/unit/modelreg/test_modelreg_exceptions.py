"""Tests for :mod:`eaip.modelreg.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.modelreg.exceptions import (
    ModelNotFoundError,
    ModelRegistryError,
    ModelVersionConflictError,
)


class TestModelRegistryExceptionHierarchy:
    """Tests for the model registry exception hierarchy."""

    def test_registry_error_is_eaip_error(self) -> None:
        """Test that ModelRegistryError extends EAIPError."""
        assert issubclass(ModelRegistryError, EAIPError)

    def test_not_found_is_registry_error(self) -> None:
        """Test that ModelNotFoundError extends ModelRegistryError."""
        assert issubclass(ModelNotFoundError, ModelRegistryError)

    def test_version_conflict_is_registry_error(self) -> None:
        """Test that ModelVersionConflictError extends ModelRegistryError."""
        assert issubclass(ModelVersionConflictError, ModelRegistryError)


class TestErrorCodes:
    """Tests for error codes on model registry exceptions."""

    def test_registry_error_code(self) -> None:
        """Test the default error code for ModelRegistryError."""
        err = ModelRegistryError("test")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_not_found_code(self) -> None:
        """Test the default error code for ModelNotFoundError."""
        err = ModelNotFoundError("not found")
        assert err.code == ErrorCode.MODEL_NOT_FOUND

    def test_version_conflict_code(self) -> None:
        """Test the default error code for ModelVersionConflictError."""
        err = ModelVersionConflictError("conflict")
        assert err.code == ErrorCode.REGISTRY_DUPLICATE


class TestErrorMessage:
    """Tests for error messages on model registry exceptions."""

    def test_message_preserved(self) -> None:
        """Test that the error message is preserved."""
        err = ModelNotFoundError("Custom message")
        assert str(err) == "Custom message"

    def test_context_supported(self) -> None:
        """Test that context is supported on exceptions."""
        err = ModelRegistryError("error", context={"model_id": "m1"})
        assert err.context["model_id"] == "m1"
