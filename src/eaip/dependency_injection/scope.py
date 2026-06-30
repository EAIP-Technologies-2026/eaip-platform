"""Provider scopes supported by the container."""

from __future__ import annotations

from enum import StrEnum


class Scope(StrEnum):
    """How long a provider's cached instance lives.

    * ``SINGLETON`` — built once per container, reused forever.
    * ``TRANSIENT`` — rebuilt on every resolution.
    * ``SCOPED`` — built once per ``Container.create_scope()`` child container.
    """

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


__all__ = ["Scope"]
