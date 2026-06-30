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
        self._environ = environ if environ is not None else os.environ

    def get(self, name: str) -> str | None:
        if not name:
            raise ValueError("secret name must be non-empty")
        return self._environ.get(name)

    def require(self, name: str) -> str:
        value = self.get(name)
        if value is None:
            raise NotFoundError(
                f"required secret {name!r} not present in environment",
                context={"secret": name},
            )
        return value


__all__ = ["EnvSecretProvider"]
