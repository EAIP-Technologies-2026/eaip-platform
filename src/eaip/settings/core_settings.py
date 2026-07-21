"""Platform-wide settings model — the root configuration object."""

from __future__ import annotations

from typing import Self

from pydantic import Field

from eaip.logging.config import LogFormat, LoggingConfig
from eaip.settings.base import EAIPSettingsBase
from eaip.settings.db_settings import DatabaseSettings
from eaip.types import Environment, EnvName, NonEmptyStr


class LoggingSettings(EAIPSettingsBase):
    """Settings nested under ``EAIP_LOGGING_*`` (mapped from :class:`LoggingConfig`)."""

    level: str = Field(default="INFO")
    format: LogFormat = Field(default="json")
    include_caller: bool = Field(default=False)

    def to_logging_config(self: Self) -> LoggingConfig:
        """Map this settings instance to a full :class:`LoggingConfig`."""
        return LoggingConfig(
            level=self.level,
            format=self.format,
            include_caller=self.include_caller,
        )


class FeatureFlagSettings(EAIPSettingsBase):
    """Static feature-flag overrides. Dynamic flags live in :mod:`eaip.core.feature_flags`."""

    enabled: tuple[str, ...] = Field(default=())
    disabled: tuple[str, ...] = Field(default=())


class CoreSettings(EAIPSettingsBase):
    """Identity & environment of the running platform."""

    app_name: NonEmptyStr = Field(default="eaip-platform")
    environment: Environment = Field(default=Environment.LOCAL)
    environment_name: EnvName = Field(default="local")
    instance_id: NonEmptyStr = Field(default="local-0")
    debug: bool = Field(default=False)


class TelemetrySettings(EAIPSettingsBase):
    """Settings for OpenTelemetry export.

    Read from ``EAIP_TELEMETRY_*`` environment variables.
    """

    service_name: str = Field(default="eaip")
    otlp_endpoint: str = Field(default="http://localhost:4318")
    otlp_protocol: str = Field(default="http/protobuf")
    sampling_ratio: float = Field(default=1.0, ge=0.0, le=1.0)
    tracing_enabled: bool = Field(default=True)
    metrics_enabled: bool = Field(default=True)


class PlatformSettings(EAIPSettingsBase):
    """The root settings object exposed via :func:`load_platform_settings`."""

    core: CoreSettings = Field(default_factory=CoreSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    feature_flags: FeatureFlagSettings = Field(default_factory=FeatureFlagSettings)
    telemetry: TelemetrySettings = Field(default_factory=TelemetrySettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)


def load_platform_settings() -> PlatformSettings:
    """Load :class:`PlatformSettings` from environment variables.

    A thin helper kept independent of :mod:`eaip.config` so that callers who
    only want env-driven settings can bypass the layered loader entirely.
    """
    return PlatformSettings()


__all__ = [
    "CoreSettings",
    "FeatureFlagSettings",
    "LoggingSettings",
    "PlatformSettings",
    "TelemetrySettings",
    "load_platform_settings",
]
