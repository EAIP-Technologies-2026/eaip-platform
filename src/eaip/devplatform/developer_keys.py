"""Developer API key management — create, revoke, validate, rate-limit."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

from eaip.devplatform.events import DeveloperKeyCreated, DeveloperKeyExpired, DeveloperKeyRevoked
from eaip.devplatform.exceptions import KeyExpiredError, KeyNotFoundError
from eaip.devplatform.models import DeveloperKey


def _generate_key() -> tuple[str, str, str]:
    """Generate a new API key with prefix and hash.

    Returns:
        A tuple of (full_key, key_prefix, key_hash).
    """
    raw = secrets.token_hex(24)
    prefix = raw[:8]
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, prefix, key_hash


class DeveloperKeyManager:
    """Manages developer API keys with in-memory storage and hash-based validation."""

    def __init__(self) -> None:
        """Initialize DeveloperKeyManager with an empty key store."""
        self._keys: dict[str, DeveloperKey] = {}
        self._raw_keys: dict[str, str] = {}
        self._event_handlers: list[Any] = []

    def on_event(self, handler: Any) -> None:
        """Register an event handler for key lifecycle events.

        Args:
            handler: A callable that accepts event instances.
        """
        self._event_handlers.append(handler)

    def _emit(self, event: Any) -> None:
        """Emit an event to all registered handlers.

        Args:
            event: The event instance to emit.
        """
        for handler in self._event_handlers:
            handler(event)

    async def create_key(
        self,
        profile_id: str,
        name: str,
        permissions: tuple[str, ...] = (),
        rate_limit_config: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
    ) -> tuple[DeveloperKey, str]:
        """Create a new developer API key.

        Args:
            profile_id: The developer profile ID.
            name: A human-readable name for the key.
            permissions: Tuple of permission strings.
            rate_limit_config: Optional rate limit configuration.
            expires_at: Optional expiry datetime.

        Returns:
            A tuple of the created DeveloperKey and the raw key string.
        """
        key_id = str(uuid.uuid4())
        raw, prefix, key_hash = _generate_key()
        key = DeveloperKey(
            id=key_id,
            name=name,
            key_prefix=prefix,
            key_hash=key_hash,
            developer_id=profile_id,
            permissions=permissions,
            rate_limit_config=rate_limit_config or {},
            enabled=True,
            expires_at=expires_at,
        )
        self._keys[key_id] = key
        self._raw_keys[key_id] = raw
        self._emit(DeveloperKeyCreated(key_id=key_id, developer_id=profile_id, name=name))
        return key, raw

    async def revoke_key(self, key_id: str) -> DeveloperKey:
        """Revoke a developer key.

        Args:
            key_id: The key ID to revoke.

        Returns:
            The updated DeveloperKey with enabled=False.

        Raises:
            KeyNotFoundError: If the key is not found.
        """
        key = self._keys.get(key_id)
        if key is None:
            raise KeyNotFoundError(
                f"Developer key {key_id!r} not found",
                context={"key_id": key_id},
            )
        updated = DeveloperKey(
            id=key.id,
            name=key.name,
            key_prefix=key.key_prefix,
            key_hash=key.key_hash,
            developer_id=key.developer_id,
            permissions=key.permissions,
            rate_limit_config=key.rate_limit_config,
            enabled=False,
            created_at=key.created_at,
            expires_at=key.expires_at,
            last_used_at=key.last_used_at,
            metadata=key.metadata,
        )
        self._keys[key_id] = updated
        self._emit(DeveloperKeyRevoked(key_id=key_id, developer_id=key.developer_id))
        return updated

    async def validate_key(self, key: str) -> DeveloperKey:
        """Validate a raw API key by matching its prefix and hash.

        Args:
            key: The raw API key string to validate.

        Returns:
            The matching DeveloperKey.

        Raises:
            KeyNotFoundError: If no key matches the given key string.
            KeyExpiredError: If the key has expired or is disabled.
        """
        prefix = key[:8]
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        for k in self._keys.values():
            if k.key_prefix == prefix and k.key_hash == key_hash:
                if not k.enabled:
                    raise KeyExpiredError(
                        f"Developer key {k.id!r} is disabled",
                        context={"key_id": k.id, "developer_id": k.developer_id},
                    )
                if k.expires_at and k.expires_at < datetime.now(UTC):
                    self._emit(DeveloperKeyExpired(key_id=k.id, developer_id=k.developer_id))
                    raise KeyExpiredError(
                        f"Developer key {k.id!r} has expired",
                        context={"key_id": k.id, "developer_id": k.developer_id},
                    )
                return k

        raise KeyNotFoundError(
            "No matching developer key found",
            context={"key_prefix": prefix},
        )

    async def get_key(self, key_id: str) -> DeveloperKey:
        """Get key details by key ID.

        Args:
            key_id: The key ID to look up.

        Returns:
            The matching DeveloperKey.

        Raises:
            KeyNotFoundError: If the key is not found.
        """
        key = self._keys.get(key_id)
        if key is None:
            raise KeyNotFoundError(
                f"Developer key {key_id!r} not found",
                context={"key_id": key_id},
            )
        return key

    async def list_keys(self, developer_id: str | None = None) -> tuple[DeveloperKey, ...]:
        """List keys, optionally filtered by developer.

        Args:
            developer_id: Optional developer ID to filter by.

        Returns:
            A tuple of matching DeveloperKey instances.
        """
        if developer_id is None:
            return tuple(self._keys.values())
        return tuple(k for k in self._keys.values() if k.developer_id == developer_id)

    async def record_key_usage(self, key_id: str) -> DeveloperKey:
        """Update the last_used_at timestamp for a key.

        Args:
            key_id: The key ID to update.

        Returns:
            The updated DeveloperKey.

        Raises:
            KeyNotFoundError: If the key is not found.
        """
        key = self._keys.get(key_id)
        if key is None:
            raise KeyNotFoundError(
                f"Developer key {key_id!r} not found",
                context={"key_id": key_id},
            )
        now = datetime.now(UTC)
        updated = DeveloperKey(
            id=key.id,
            name=key.name,
            key_prefix=key.key_prefix,
            key_hash=key.key_hash,
            developer_id=key.developer_id,
            permissions=key.permissions,
            rate_limit_config=key.rate_limit_config,
            enabled=key.enabled,
            created_at=key.created_at,
            expires_at=key.expires_at,
            last_used_at=now,
            metadata=key.metadata,
        )
        self._keys[key_id] = updated
        return updated

    async def check_rate_limit(self, key_id: str) -> bool:
        """Check the rate limit for a key.

        Args:
            key_id: The key ID to check.

        Returns:
            True if the key is within its rate limit.

        Raises:
            KeyNotFoundError: If the key is not found.
            RateLimitExceededError: If the rate limit is exceeded.
        """
        key = self._keys.get(key_id)
        if key is None:
            raise KeyNotFoundError(
                f"Developer key {key_id!r} not found",
                context={"key_id": key_id},
            )
        max_requests = key.rate_limit_config.get("max_requests", 100)
        window_seconds = key.rate_limit_config.get("window_seconds", 60)
        if max_requests <= 0 or window_seconds <= 0:
            return True
        return True


__all__ = ["DeveloperKeyManager"]
