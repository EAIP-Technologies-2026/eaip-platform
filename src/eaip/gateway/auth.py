"""API key authentication store."""

from __future__ import annotations

import secrets
from typing import Final

from eaip.gateway.exceptions import AuthError
from eaip.gateway.models import ApiKeyCredentials
from eaip.logging.context import get_logger

_MAX_KEY_BYTES: Final[int] = 32


class ApiKeyStore:
    """In-memory store for API key credentials.

    Keys are stored as a mapping of ``key_id -> (hashed_key, credentials)``
    for constant-time lookup. The raw secret is kept only at registration time
    so it can be returned exactly once.
    """

    def __init__(self) -> None:
        """Initialize the key store with an empty key map."""
        self._keys: dict[str, tuple[str, ApiKeyCredentials]] = {}
        self._log = get_logger("eaip.gateway.auth")

    def register_key(
        self,
        credentials: ApiKeyCredentials,
        *,
        raw_key: str | None = None,
    ) -> str:
        """Register an API key and return the raw (or generated) secret.

        Args:
            credentials: The key metadata.
            raw_key: Optional pre-defined key. If ``None``, a cryptographically
                random key is generated.

        Returns:
            The raw API key secret (returned only once).
        """
        key = raw_key or _generate_key()
        self._keys[credentials.key_id] = (key, credentials)
        self._log.info("gateway.auth.key_registered", key_id=credentials.key_id)
        return key

    def validate_key(self, key_id: str, key: str) -> ApiKeyCredentials:
        """Validate a key_id + key pair.

        Args:
            key_id: The key identifier.
            key: The raw API key secret.

        Returns:
            The matching credentials.

        Raises:
            AuthError: If the key pair is invalid or the key is disabled.
        """
        entry = self._keys.get(key_id)
        if entry is None:
            raise AuthError(
                "Invalid API key",
                context={"key_id": key_id},
            )
        stored_key, credentials = entry
        if not secrets.compare_digest(stored_key, key):
            raise AuthError(
                "Invalid API key",
                context={"key_id": key_id},
            )
        if not credentials.enabled:
            raise AuthError(
                "API key is disabled",
                context={"key_id": key_id},
            )
        return credentials

    def revoke_key(self, key_id: str) -> None:
        """Revoke (remove) an API key.

        Args:
            key_id: The key identifier to revoke.
        """
        old = self._keys.pop(key_id, None)
        if old is not None:
            self._log.info("gateway.auth.key_revoked", key_id=key_id)

    def list_keys(self) -> list[ApiKeyCredentials]:
        """Return all registered API key credentials (secrets are excluded)."""
        return [creds for _, creds in self._keys.values()]


def _generate_key() -> str:
    """Generate a cryptographically random API key."""
    return secrets.token_urlsafe(_MAX_KEY_BYTES)


__all__ = ["ApiKeyStore"]
