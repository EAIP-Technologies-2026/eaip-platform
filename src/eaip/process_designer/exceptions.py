"""Exception hierarchy for the process designer."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ProcessDesignError(EAIPError):
    """Base exception for all process designer errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ProcessModelNotFoundError(ProcessDesignError):
    """Raised when a process model is not found."""

    default_code = ErrorCode.NOT_FOUND

    def __init__(self, model_id: str) -> None:
        """Initialize with the missing model ID."""
        self.model_id = model_id
        super().__init__(f"process model not found: {model_id!r}")


class ProcessValidationError(ProcessDesignError):
    """Raised when process model validation fails."""

    default_code = ErrorCode.VALIDATION_FAILED

    def __init__(self, message: str = "process validation failed") -> None:
        """Initialize with an optional error message."""
        super().__init__(message)


class ProcessPublishError(ProcessDesignError):
    """Raised when a process model cannot be published."""

    default_code = ErrorCode.LIFECYCLE_FORBIDDEN

    def __init__(self, message: str = "process model could not be published") -> None:
        """Initialize with an optional error message."""
        super().__init__(message)


class ProcessSimulationError(ProcessDesignError):
    """Raised when process simulation fails."""

    default_code = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str = "process simulation failed") -> None:
        """Initialize with an optional error message."""
        super().__init__(message)


class ElementNotFoundError(ProcessDesignError):
    """Raised when a process element is not found."""

    default_code = ErrorCode.NOT_FOUND

    def __init__(self, element_id: str) -> None:
        """Initialize with the missing element ID."""
        self.element_id = element_id
        super().__init__(f"element not found: {element_id!r}")


class ConnectorValidationError(ProcessDesignError):
    """Raised when a connector fails validation."""

    default_code = ErrorCode.VALIDATION_FAILED

    def __init__(self, message: str = "connector validation failed") -> None:
        """Initialize with an optional error message."""
        super().__init__(message)


class ProcessExportError(ProcessDesignError):
    """Raised when process model export fails."""

    default_code = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str = "process model export failed") -> None:
        """Initialize with an optional error message."""
        super().__init__(message)


class ProcessImportError(ProcessDesignError):
    """Raised when process model import fails."""

    default_code = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str = "process model import failed") -> None:
        """Initialize with an optional error message."""
        super().__init__(message)


__all__ = [
    "ConnectorValidationError",
    "ElementNotFoundError",
    "ProcessDesignError",
    "ProcessExportError",
    "ProcessImportError",
    "ProcessModelNotFoundError",
    "ProcessPublishError",
    "ProcessSimulationError",
    "ProcessValidationError",
]
