from __future__ import annotations

from typing import Any, Protocol

__all__ = ["ObservabilityProvider"]


class ObservabilityProvider(Protocol):
    """Pluggable observability backend contract.

    Implementations may back error tracking, performance monitoring,
    incident management, log export, or any combination thereof.
    """

    name: str

    def start(self) -> None:
        """Start the provider (idempotent).

        Called once during application startup.
        """
        ...

    def stop(self) -> None:
        """Stop the provider (idempotent).

        Called during application shutdown.
        """
        ...

    def is_healthy(self) -> bool:
        """Return True if the provider is operational."""
        ...

    def capture_error(self, error: Exception, context: dict[str, Any] | None = None) -> str | None:
        """Report an error event.

        Args:
            error: The exception to capture.
            context: Optional additional context.

        Returns:
            Event ID if captured, None otherwise.
        """
        ...

    def capture_message(self, message: str, level: str = "info", context: dict[str, Any] | None = None) -> str | None:
        """Report a message event.

        Args:
            message: The message to report.
            level: The severity level.
            context: Optional additional context.

        Returns:
            Event ID if captured, None otherwise.
        """
        ...

    def capture_deployment(self, release: str, environment: str) -> str | None:
        """Report a deployment event.

        Args:
            release: The release version.
            environment: The deployment environment.

        Returns:
            Event ID if captured, None otherwise.
        """
        ...

    def set_tag(self, key: str, value: str) -> None:
        """Attach a tag to all subsequent events."""
        ...