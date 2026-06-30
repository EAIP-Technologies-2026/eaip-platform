"""Secret-provider port."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SecretProviderPort(Protocol):
    """Provides secret values by name without exposing the backing store."""

    def get(self, name: str) -> str | None: ...

    def require(self, name: str) -> str: ...


__all__ = ["SecretProviderPort"]
