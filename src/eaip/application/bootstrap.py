"""Convenience bootstrap — sane defaults for typical hosts."""

from __future__ import annotations

from collections.abc import Iterable

from eaip.platform.builder import PlatformBuilder
from eaip.platform.platform import Platform
from eaip.plugins.plugin import Plugin
from eaip.settings.core_settings import PlatformSettings, load_platform_settings


def build_platform(
    *,
    settings: PlatformSettings | None = None,
    plugins: Iterable[Plugin] = (),
    configure_logging: bool = True,
) -> Platform:
    """Build a :class:`Platform` with the most common configuration.

    Parameters
    ----------
    settings:
        Optional pre-built settings. If omitted, settings are loaded from the
        environment via :func:`load_platform_settings`.
    plugins:
        Plugins to install before activation. They are activated when the
        platform starts.
    configure_logging:
        Whether the builder should call :func:`configure_logging` for you
        based on settings. Set ``False`` if your host configures logging.
    """
    builder = PlatformBuilder().with_settings(settings or load_platform_settings())
    if not configure_logging:
        builder = builder.without_logging_configuration()
    for plugin in plugins:
        builder = builder.with_plugin(plugin)
    return builder.build()


__all__ = ["build_platform"]
