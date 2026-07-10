"""Configuration manager — in-memory overlay on top of PlatformSettings."""

from __future__ import annotations

from typing import Any

from eaip.admin.events import ConfigChanged
from eaip.admin.exceptions import ConfigNotFoundError
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.settings.core_settings import PlatformSettings


class ConfigManager:
    """In-memory configuration overlay over :class:`PlatformSettings`.

    Provides get/set/list operations with optional audit logging via the
    event bus. Changes are ephemeral (in-memory only) until the application
    persists them.
    """

    def __init__(
        self,
        settings: PlatformSettings | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize ConfigManager.

        Args:
            settings: The platform settings to overlay on top of.
            event_bus: Optional event bus for publishing ConfigChanged events.
        """
        self._settings = settings or PlatformSettings()
        self._overlay: dict[str, Any] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.admin.config")

    def get(self, key: str) -> Any:
        """Retrieve a configuration value.

        Checks the in-memory overlay first, then falls through to
        PlatformSettings.

        Args:
            key: Dot-separated configuration path (e.g. ``core.app_name``).

        Returns:
            The configuration value.

        Raises:
            ConfigNotFoundError: If the key is not found.
        """
        if key in self._overlay:
            return self._overlay[key]
        try:
            parts = key.split(".")
            obj: Any = self._settings
            for part in parts:
                obj = getattr(obj, part)
            return obj
        except AttributeError as exc:
            raise ConfigNotFoundError(
                f"Configuration key {key!r} not found",
                context={"key": key},
            ) from exc

    def set(self, key: str, value: Any, changed_by: str = "system") -> None:
        """Set a configuration value in the in-memory overlay.

        Args:
            key: Dot-separated configuration path.
            value: The value to set.
            changed_by: Identifier of the entity making the change.
        """
        old_value = self._overlay.get(key)
        self._overlay[key] = value
        self._log.info("config.set", key=key, changed_by=changed_by)

        if self._event_bus is not None:
            import asyncio

            event = ConfigChanged(
                key=key,
                old_value=old_value,
                new_value=value,
                changed_by=changed_by,
            )
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(self._event_bus.publish(event))
            except RuntimeError:
                pass

    def list(self) -> dict[str, Any]:
        """List all known configuration entries.

        Returns:
            A flat dictionary of merged overlay and settings entries.
        """
        result: dict[str, Any] = {}
        settings_dict = self._settings.model_dump()
        self._flatten(settings_dict, "", result)
        result.update(self._overlay)
        return result

    async def reload(self) -> None:
        """Reload from PlatformSettings, discarding the in-memory overlay."""
        self._overlay.clear()
        self._settings = PlatformSettings()
        self._log.info("config.reloaded")

    @staticmethod
    def _flatten(
        d: dict[str, Any],
        prefix: str,
        result: dict[str, Any],
    ) -> None:
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                ConfigManager._flatten(v, key, result)
            else:
                result[key] = v
