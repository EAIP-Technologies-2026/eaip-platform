"""Base settings class — opinionated defaults shared by every settings model."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class EAIPSettingsBase(BaseSettings):
    """Project-wide ``BaseSettings`` parent.

    Subclasses inherit:

    * ``EAIP_`` environment prefix.
    * ``__`` nested-key delimiter.
    * Case-insensitive variable matching.
    * Extra fields forbidden — typos fail fast.
    * Validation on assignment (mutable patterns at boot stay correct).
    """

    model_config = SettingsConfigDict(
        env_prefix="EAIP_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="forbid",
        validate_assignment=True,
        frozen=False,
    )


__all__ = ["EAIPSettingsBase"]
