"""Default :class:`SecretProviderPort` implementation backed by environment variables.

This is the lowest-common-denominator secret provider; production deployments
swap it for a vault-backed adapter via the DI container.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from eaip.exceptions.domain import NotFoundError
from eaip.ports.secret_provider import SecretProviderPort


class EnvSecretProvider(SecretProviderPort):
    """Resolves secrets from ``os.environ`` (or any mapping)."""

    __slots__ = ("_environ",)

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        """Initializes a new EnvSecretProvider.

        Args:
            environ: A mapping to use for secret resolution. Defaults to os.environ.
        """
        self._environ = environ if environ is not None else os.environ

    def get(self, name: str) -> str | None:
        """Resolves a secret by name.

        Args:
            name: The name of the secret to resolve.

        Returns:
            The secret value, or None if not found.

        Raises:
            ValueError: If the secret name is empty.
        """
        if not name:
            raise ValueError("secret name must be non-empty")
        return self._environ.get(name)

    def require(self, name: str) -> str:
        """Resolves a mandatory secret by name.

        Args:
            name: The name of the secret to resolve.

        Returns:
            The secret value.

        Raises:
            NotFoundError: If the secret is not found.
        """
        value = self.get(name)
        if value is None:
            raise NotFoundError(
                f"required secret {name!r} not present in environment",
                context={"secret": name},
            )
        return value


__all__ = ["EnvSecretProvider"]
