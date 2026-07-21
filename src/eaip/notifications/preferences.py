"""Preference manager — per-user notification channel preferences and quiet-hours."""

from __future__ import annotations

from datetime import datetime, time

from eaip.logging.context import get_logger
from eaip.notifications.events import PreferenceUpdated
from eaip.notifications.models import NotificationChannel, NotificationPreference
from eaip.shared.time import utc_now


class PreferenceManager:
    """Manages per-user notification channel preferences."""

    def __init__(self) -> None:
        self._preferences: dict[str, NotificationPreference] = {}
        self._daily_counts: dict[str, int] = {}
        self._log = get_logger("eaip.notifications.preferences")
        self._events: list[PreferenceUpdated] = []
        self._last_reset: datetime = utc_now()

    def set_preference(
        self,
        user_id: str,
        channel: NotificationChannel,
        enabled: bool = True,
        quiet_hours_start: str | None = None,
        quiet_hours_end: str | None = None,
        max_daily: int | None = None,
    ) -> NotificationPreference:
        pref = NotificationPreference(
            user_id=user_id,
            channel=channel,
            enabled=enabled,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
            max_daily=max_daily,
        )
        key = f"{user_id}:{channel.value}"
        self._preferences[key] = pref
        self._events.append(
            PreferenceUpdated(user_id=user_id, channel=channel.value, enabled=enabled)
        )
        self._log.info("notification.preference.updated", user_id=user_id, channel=channel.value)
        return pref

    def get_preference(
        self, user_id: str, channel: NotificationChannel
    ) -> NotificationPreference | None:
        return self._preferences.get(f"{user_id}:{channel.value}")

    def get_preferences(self, user_id: str) -> list[NotificationPreference]:
        return [p for key, p in self._preferences.items() if key.startswith(f"{user_id}:")]

    def check_channel_allowed(self, user_id: str, channel: NotificationChannel) -> bool:
        pref = self.get_preference(user_id, channel)
        if pref is None:
            return True
        if not pref.enabled:
            return False
        if self._in_quiet_hours(pref):
            return False
        if pref.max_daily is not None:
            count = self._daily_counts.get(f"{user_id}:{channel.value}", 0)
            if count >= pref.max_daily:
                return False
        return True

    def get_quiet_hours_status(
        self, user_id: str, channel: NotificationChannel
    ) -> dict[str, bool | str | None]:
        pref = self.get_preference(user_id, channel)
        if pref is None or not pref.quiet_hours_start or not pref.quiet_hours_end:
            return {"in_quiet_hours": False, "start": None, "end": None}
        return {
            "in_quiet_hours": self._in_quiet_hours(pref),
            "start": pref.quiet_hours_start,
            "end": pref.quiet_hours_end,
        }

    def get_daily_count(self, user_id: str, channel: NotificationChannel) -> int:
        now = utc_now()
        if now.date() > self._last_reset.date():
            self._daily_counts.clear()
            self._last_reset = now
        return self._daily_counts.get(f"{user_id}:{channel.value}", 0)

    def increment_daily_count(self, user_id: str, channel: NotificationChannel) -> None:
        key = f"{user_id}:{channel.value}"
        self._daily_counts[key] = self.get_daily_count(user_id, channel) + 1

    def drain_events(self) -> list[PreferenceUpdated]:
        events = list(self._events)
        self._events.clear()
        return events

    @staticmethod
    def _in_quiet_hours(pref: NotificationPreference) -> bool:
        if not pref.quiet_hours_start or not pref.quiet_hours_end:
            return False
        now = utc_now().time()
        start = _parse_time(pref.quiet_hours_start)
        end = _parse_time(pref.quiet_hours_end)
        if start is None or end is None:
            return False
        if start <= end:
            return start <= now <= end
        return now >= start or now <= end


def _parse_time(value: str) -> time | None:
    parts = value.split(":")
    if len(parts) == 2:
        try:
            return time(int(parts[0]), int(parts[1]))
        except (ValueError, TypeError):
            return None
    return None


__all__ = ["PreferenceManager"]
