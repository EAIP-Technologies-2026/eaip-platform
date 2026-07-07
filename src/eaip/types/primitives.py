"""Constrained primitive types for configuration & domain models.

These types are :mod:`pydantic` v2 ``Annotated`` aliases. They behave like
plain Python primitives at runtime but enforce invariants the moment they are
parsed by a Pydantic model.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, Field, StringConstraints

#: A non-empty, whitespace-trimmed string.
NonEmptyStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=4096),
]

#: A TCP port number (1-65535).
Port = Annotated[int, Field(ge=1, le=65_535)]

MAX_HOSTNAME_LENGTH = 253


def _validate_host(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("host name must not be empty")
    if any(ch.isspace() for ch in value):
        raise ValueError("host name must not contain whitespace")
    if len(value) > MAX_HOSTNAME_LENGTH:
        raise ValueError(f"host name exceeds {MAX_HOSTNAME_LENGTH} characters")
    return value


HostName = Annotated[str, AfterValidator(_validate_host)]


def _validate_url(value: str) -> str:
    value = value.strip()
    if "://" not in value:
        raise ValueError(f"invalid URL {value!r}: missing scheme")
    scheme, _, rest = value.partition("://")
    if not scheme or not rest:
        raise ValueError(f"invalid URL {value!r}")
    return value


#: A best-effort URL string (scheme://host[/path]). Strict parsing is the
#: responsibility of each capability that needs it.
Url = Annotated[str, AfterValidator(_validate_url)]


def _validate_log_level(value: str) -> str:
    upper = value.upper()
    if upper not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError(
            f"invalid log level {value!r}: expected one of DEBUG/INFO/WARNING/ERROR/CRITICAL"
        )
    return upper


#: A canonicalised logging level name.
LogLevel = Annotated[str, AfterValidator(_validate_log_level)]


def _validate_env_name(value: str) -> str:
    value = value.strip().lower()
    if not value:
        raise ValueError("environment name must not be empty")
    if not all(c.isalnum() or c in "-_" for c in value):
        raise ValueError(f"invalid env name {value!r}: only alphanumerics, '-' and '_' allowed")
    return value


#: A free-form environment name (e.g. ``"prod-eu-west-1"``).
EnvName = Annotated[str, AfterValidator(_validate_env_name)]


__all__ = ["EnvName", "HostName", "LogLevel", "NonEmptyStr", "Port", "Url"]
