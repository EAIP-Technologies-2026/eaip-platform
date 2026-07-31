"""Platform-wide settings model — the root configuration object."""

from __future__ import annotations

from typing import Self

from pydantic import Field

from eaip.logging.config import LogFormat, LoggingConfig
from eaip.settings.base import EAIPSettingsBase
from eaip.settings.db_settings import DatabaseProviderSettings, DatabaseSettings
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


class SentrySettings(EAIPSettingsBase):
    """Settings for Sentry error tracking and performance monitoring.

    Read from ``EAIP_SENTRY_*`` environment variables.
    """

    dsn: str | None = Field(default=None)
    environment: str | None = Field(default=None)
    release: str | None = Field(default=None)
    traces_sample_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    traces_sampler_debug_enabled: bool = Field(default=False)
    send_default_pii: bool = Field(default=False)
    attach_stacktrace: bool = Field(default=True)
    profile_life_cycle: str = Field(default="auto")
    send_reports: bool = Field(default=True)


class BetterStackSettings(EAIPSettingsBase):
    """Settings for Better Stack incident management and observability.

    Read from ``EAIP_BESTACK_*`` environment variables.
    """

    api_key: str | None = Field(default=None)
    organization: str | None = Field(default=None)
    project: str | None = Field(default=None)
    enabled: bool = Field(default=False)
    status_page_url: str | None = Field(default=None)


class ReleaseSettings(EAIPSettingsBase):
    """Release metadata for observability providers.

    Read from ``EAIP_RELEASE_*`` environment variables.
    """

    version: str | None = Field(default=None)
    environment: str | None = Field(default=None)
    commit: str | None = Field(default=None)
    branch: str | None = Field(default=None)
    deployed_by: str | None = Field(default=None)


class PlatformSettings(EAIPSettingsBase):
    """The root settings object exposed via :func:`load_platform_settings`."""

    core: CoreSettings = Field(default_factory=CoreSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    feature_flags: FeatureFlagSettings = Field(default_factory=FeatureFlagSettings)
    telemetry: TelemetrySettings = Field(default_factory=TelemetrySettings)
    sentry: SentrySettings = Field(default_factory=SentrySettings)
    better_stack: BetterStackSettings = Field(default_factory=BetterStackSettings)
    release: ReleaseSettings = Field(default_factory=ReleaseSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    database_provider: DatabaseProviderSettings = Field(default_factory=DatabaseProviderSettings)


def load_platform_settings() -> PlatformSettings:
    """Load :class:`PlatformSettings` from environment variables.

    A thin helper kept independent of :mod:`eaip.config` so that callers who
    only want env-driven settings can bypass the layered loader entirely.
    """
    return PlatformSettings()


__all__ = [
    "BetterStackSettings",
    "CoreSettings",
    "FeatureFlagSettings",
    "LoggingSettings",
    "PlatformSettings",
    "ReleaseSettings",
    "SentrySettings",
    "TelemetrySettings",
    "load_platform_settings",
]
