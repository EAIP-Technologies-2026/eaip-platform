"""Token service — JWT creation, validation, refresh, revocation, and lifecycle management."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from eaip.auth.events import (
    TokenCreated,
    TokenExpired,
    TokenRefreshed,
    TokenRevoked,
    TokenValidated,
)
from eaip.auth.exceptions import TokenInvalidError
from eaip.auth.models import AuthToken, TokenConfig, TokenStatus, TokenType
from eaip.events.bus import EventBus
from eaip.infrastructure.secret_provider import EnvSecretProvider
from eaip.ports.secret_provider import SecretProviderPort
from eaip.shared.repository import InMemoryRepository


def _generate_token_id() -> str:
    return uuid.uuid4().hex


def _hash_token(token_string: str) -> str:
    return hashlib.sha256(token_string.encode()).hexdigest()


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64_decode(data: str) -> bytes:
    padded = data + "=" * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(padded)


def _create_jwt(payload: dict[str, Any], secret: str, algorithm: str = "HS256") -> str:
    header = {"alg": algorithm, "typ": "JWT"}
    header_b64 = _b64_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}"
    if algorithm == "HS256":
        sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    else:
        sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha512).digest()
    return f"{signing_input}.{_b64_encode(sig)}"


def _parse_jwt(token_string: str, secret: str, algorithm: str = "HS256") -> dict[str, Any]:
    parts = token_string.split(".")
    if len(parts) != 3:
        raise TokenInvalidError("Malformed token")
    header_b64, payload_b64, sig_b64 = parts
    try:
        signing_input = f"{header_b64}.{payload_b64}"
        if algorithm == "HS256":
            expected_sig = hmac.new(
                secret.encode(), signing_input.encode(), hashlib.sha256
            ).digest()
        else:
            expected_sig = hmac.new(
                secret.encode(), signing_input.encode(), hashlib.sha512
            ).digest()
        given_sig = _b64_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, given_sig):
            raise TokenInvalidError("Invalid token signature")
        payload_bytes = _b64_decode(payload_b64)
        result: dict[str, Any] = json.loads(payload_bytes)
        return result
    except (json.JSONDecodeError, ValueError, IndexError):
        raise TokenInvalidError("Malformed token")


def _resolve_jwt_secret(
    secret: str | None,
    provider: SecretProviderPort | None,
) -> str:
    """Resolve the JWT signing secret from explicit value or secret provider.

    Args:
        secret: An explicit secret value, or ``None`` to resolve via provider.
        provider: An optional :class:`SecretProviderPort` instance.

    Returns:
        The resolved secret.

    Raises:
        RuntimeError: If no secret can be resolved from any source.
    """
    if secret is not None:
        return secret
    prov = provider or EnvSecretProvider()
    value = prov.get("EAIP_AUTH_SECRET")
    if value is not None:
        return value
    value = prov.get("EAIP_AUTH__SECRET")
    if value is not None:
        return value
    raise RuntimeError(
        "No JWT signing secret configured. "
        "Set the EAIP_AUTH_SECRET environment variable or pass "
        "an explicit ``secret=`` argument to ``TokenService.__init__``."
    )


class TokenService:
    def __init__(
        self,
        config: TokenConfig | None = None,
        secret: str | None = None,
        secret_provider: SecretProviderPort | None = None,
        event_bus: EventBus | None = None,
        token_repository: InMemoryRepository[str, AuthToken] | None = None,
    ) -> None:
        self._config = config or TokenConfig()
        self._secret = _resolve_jwt_secret(secret, secret_provider)
        self._tokens = token_repository or InMemoryRepository[str, AuthToken](
            max_size=100_000,
            default_ttl_seconds=float((config or TokenConfig()).refresh_token_ttl_seconds * 2),
        )
        self._token_strings: dict[str, str] = {}
        self._event_bus = event_bus

    @property
    def config(self) -> TokenConfig:
        return self._config

    async def create_token(
        self,
        subject: str,
        type: TokenType,
        claims: dict[str, Any] | None = None,
        ttl: int | None = None,
    ) -> AuthToken:
        token_id = _generate_token_id()
        now = datetime.now(UTC)
        effective_ttl = ttl or (
            self._config.access_token_ttl_seconds
            if type == TokenType.ACCESS
            else self._config.refresh_token_ttl_seconds
        )
        expires_at = now + timedelta(seconds=effective_ttl)

        payload: dict[str, Any] = {
            "jti": token_id,
            "sub": subject,
            "iss": self._config.issuer,
            "aud": list(self._config.audience),
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "type": type.value,
        }
        if claims:
            payload["claims"] = claims

        token_string = _create_jwt(payload, self._secret, self._config.signing_algorithm)
        token_hash = _hash_token(token_string)

        token = AuthToken(
            id=token_id,
            type=type,
            issuer=self._config.issuer,
            subject=subject,
            audience=self._config.audience,
            claims=claims or {},
            issued_at=now,
            expires_at=expires_at,
            token_hash=token_hash,
            status=TokenStatus.ACTIVE,
        )

        await self._tokens.add(token, ttl_seconds=float(effective_ttl))
        self._token_strings[token_id] = token_string
        await self._emit(TokenCreated(token=token))
        return token

    async def validate_token(self, token_string: str) -> tuple[bool, dict[str, Any], str]:
        try:
            payload = _parse_jwt(token_string, self._secret, self._config.signing_algorithm)
        except TokenInvalidError as exc:
            await self._emit(TokenValidated(token_id="", valid=False, error=str(exc)))
            return False, {}, str(exc)

        token_id = payload.get("jti", "")
        stored = await self._tokens.get(token_id)

        if stored is None:
            err = "Token not found in store"
            await self._emit(TokenValidated(token_id=token_id, valid=False, error=err))
            return False, {}, err

        now = datetime.now(UTC)
        exp_ts = payload.get("exp", 0)
        if now.timestamp() > exp_ts:
            expired = stored.model_copy(update={"status": TokenStatus.EXPIRED})
            await self._tokens.add(expired, ttl_seconds=60.0)
            await self._emit(
                TokenExpired(
                    token_id=token_id, subject=stored.subject, token_type=stored.type.value
                )
            )
            return False, {}, "Token expired"

        if stored.status == TokenStatus.REVOKED:
            return False, {}, "Token revoked"

        if stored.status == TokenStatus.SUSPENDED:
            return False, {}, "Token suspended"

        claims = payload.get("claims", {})
        await self._emit(TokenValidated(token_id=token_id, valid=True))
        return True, claims, ""

    async def refresh_token(self, refresh_token_string: str) -> tuple[AuthToken, AuthToken]:
        valid, claims, error = await self.validate_token(refresh_token_string)
        if not valid:
            raise TokenInvalidError(f"Cannot refresh: {error}")

        payload = _parse_jwt(refresh_token_string, self._secret, self._config.signing_algorithm)
        token_id = payload.get("jti", "")
        stored = await self._tokens.get(token_id)
        if stored is None:
            raise TokenInvalidError("Refresh token not found")

        if stored.type != TokenType.REFRESH:
            raise TokenInvalidError("Token is not a refresh token")

        subject = stored.subject
        new_access = await self.create_token(
            subject=subject,
            type=TokenType.ACCESS,
            claims=claims,
        )
        new_refresh = await self.create_token(
            subject=subject,
            type=TokenType.REFRESH,
        )

        if self._config.enable_refresh_rotation:
            await self.revoke_token(token_id)

        await self._emit(
            TokenRefreshed(
                old_token_id=token_id,
                new_token_id=new_access.id,
                subject=subject,
            )
        )

        return new_access, new_refresh

    async def revoke_token(self, token_id: str) -> None:
        stored = await self._tokens.get(token_id)
        if stored is None:
            return
        revoked = stored.model_copy(update={"status": TokenStatus.REVOKED})
        await self._tokens.add(revoked, ttl_seconds=3600.0)
        await self._emit(
            TokenRevoked(
                token_id=token_id,
                subject=stored.subject,
                reason="manual_revocation",
            )
        )

    async def revoke_all_user_tokens(self, subject: str) -> None:
        to_revoke: list[str] = []
        async for token in self._tokens.iter_all():
            if token.subject == subject and token.status == TokenStatus.ACTIVE:
                to_revoke.append(token.id)
        for token_id in to_revoke:
            await self.revoke_token(token_id)

    async def get_token(self, token_id: str) -> AuthToken | None:
        return await self._tokens.get(token_id)

    async def get_token_string(self, token_id: str) -> str | None:
        return self._token_strings.get(token_id)

    async def list_tokens(
        self,
        subject: str | None = None,
        status: TokenStatus | None = None,
        limit: int = 100,
    ) -> Sequence[AuthToken]:
        results: list[AuthToken] = []
        async for token in self._tokens.iter_all():
            if subject is not None and token.subject != subject:
                continue
            if status is not None and token.status != status:
                continue
            results.append(token)
        return sorted(results, key=lambda t: t.issued_at, reverse=True)[:limit]

    async def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from the store and return the count removed."""
        return await self._tokens.cleanup_expired()

    async def _emit(self, event: Any) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)


__all__ = ["TokenService"]
