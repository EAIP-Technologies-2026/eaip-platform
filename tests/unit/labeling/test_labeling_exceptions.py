"""Tests for :mod:`eaip.labeling.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.labeling.exceptions import LabelConflictError, LabelingError, TaskNotFoundError


class TestLabelingExceptionHierarchy:
    """Tests for the labeling exception hierarchy."""

    def test_labeling_error_is_eaip_error(self) -> None:
        """Test that LabelingError extends EAIPError."""
        assert issubclass(LabelingError, EAIPError)

    def test_task_not_found_is_labeling_error(self) -> None:
        """Test that TaskNotFoundError extends LabelingError."""
        assert issubclass(TaskNotFoundError, LabelingError)

    def test_label_conflict_is_labeling_error(self) -> None:
        """Test that LabelConflictError extends LabelingError."""
        assert issubclass(LabelConflictError, LabelingError)


class TestErrorCodes:
    """Tests for error codes on labeling exceptions."""

    def test_labeling_error_code(self) -> None:
        """Test the default error code for LabelingError."""
        err = LabelingError("test")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_not_found_code(self) -> None:
        """Test the default error code for TaskNotFoundError."""
        err = TaskNotFoundError("not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_conflict_code(self) -> None:
        """Test the default error code for LabelConflictError."""
        err = LabelConflictError("conflict")
        assert err.code == ErrorCode.REGISTRY_DUPLICATE


class TestErrorMessage:
    """Tests for error messages on labeling exceptions."""

    def test_message_preserved(self) -> None:
        """Test that the error message is preserved."""
        err = TaskNotFoundError("Custom message")
        assert str(err) == "Custom message"

    def test_context_supported(self) -> None:
        """Test that context is supported on exceptions."""
        err = LabelingError("error", context={"task_id": "t1"})
        assert err.context["task_id"] == "t1"
