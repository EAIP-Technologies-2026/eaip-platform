"""Secret-provider port."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SecretProviderPort(Protocol):
    """Provides secret values by name without exposing the backing store."""

    def get(self, name: str) -> str | None:
        """Retrieves a secret value by name.

        Args:
            name: The name of the secret.

        Returns:
            The secret value, or None if not found.
        """
        ...

    def require(self, name: str) -> str:
        """Retrieves a required secret value by name.

        Args:
            name: The name of the secret.

        Returns:
            The secret value.
        """
        ...


__all__ = ["SecretProviderPort"]
