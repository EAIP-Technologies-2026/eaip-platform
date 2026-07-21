"""Tests for notification preference manager."""

from __future__ import annotations

import pytest

from eaip.notifications.events import PreferenceUpdated
from eaip.notifications.models import NotificationChannel
from eaip.notifications.preferences import PreferenceManager


class TestPreferenceManager:
    @pytest.fixture
    def manager(self) -> PreferenceManager:
        return PreferenceManager()

    def test_set_preference(self, manager: PreferenceManager) -> None:
        pref = manager.set_preference("u1", NotificationChannel.EMAIL, enabled=True)
        assert pref.user_id == "u1"
        assert pref.channel == NotificationChannel.EMAIL
        assert pref.enabled is True

    def test_set_preference_with_quiet_hours(self, manager: PreferenceManager) -> None:
        pref = manager.set_preference(
            "u1",
            NotificationChannel.EMAIL,
            quiet_hours_start="22:00",
            quiet_hours_end="07:00",
            max_daily=5,
        )
        assert pref.quiet_hours_start == "22:00"
        assert pref.quiet_hours_end == "07:00"
        assert pref.max_daily == 5

    def test_get_preference(self, manager: PreferenceManager) -> None:
        manager.set_preference("u1", NotificationChannel.EMAIL)
        pref = manager.get_preference("u1", NotificationChannel.EMAIL)
        assert pref is not None
        assert pref.user_id == "u1"

    def test_get_preference_missing(self, manager: PreferenceManager) -> None:
        pref = manager.get_preference("nonexistent", NotificationChannel.EMAIL)
        assert pref is None

    def test_get_preferences(self, manager: PreferenceManager) -> None:
        manager.set_preference("u1", NotificationChannel.EMAIL)
        manager.set_preference("u1", NotificationChannel.SMS)
        prefs = manager.get_preferences("u1")
        assert len(prefs) == 2

    def test_check_channel_allowed_default(self, manager: PreferenceManager) -> None:
        assert manager.check_channel_allowed("u1", NotificationChannel.EMAIL) is True

    def test_check_channel_allowed_disabled(self, manager: PreferenceManager) -> None:
        manager.set_preference("u1", NotificationChannel.EMAIL, enabled=False)
        assert manager.check_channel_allowed("u1", NotificationChannel.EMAIL) is False

    def test_check_channel_allowed_max_daily(self, manager: PreferenceManager) -> None:
        manager.set_preference("u1", NotificationChannel.EMAIL, max_daily=1)
        assert manager.check_channel_allowed("u1", NotificationChannel.EMAIL) is True
        manager.increment_daily_count("u1", NotificationChannel.EMAIL)
        assert manager.check_channel_allowed("u1", NotificationChannel.EMAIL) is False

    def test_increment_daily_count(self, manager: PreferenceManager) -> None:
        assert manager.get_daily_count("u1", NotificationChannel.EMAIL) == 0
        manager.increment_daily_count("u1", NotificationChannel.EMAIL)
        assert manager.get_daily_count("u1", NotificationChannel.EMAIL) == 1

    def test_get_quiet_hours_status_no_pref(self, manager: PreferenceManager) -> None:
        status = manager.get_quiet_hours_status("u1", NotificationChannel.EMAIL)
        assert status["in_quiet_hours"] is False

    def test_get_quiet_hours_status_no_quiet_hours(self, manager: PreferenceManager) -> None:
        manager.set_preference("u1", NotificationChannel.EMAIL)
        status = manager.get_quiet_hours_status("u1", NotificationChannel.EMAIL)
        assert status["in_quiet_hours"] is False
        assert status["start"] is None

    def test_set_preference_emits_event(self, manager: PreferenceManager) -> None:
        manager.set_preference("u1", NotificationChannel.EMAIL, enabled=False)
        events = manager.drain_events()
        assert len(events) == 1
        assert isinstance(events[0], PreferenceUpdated)
        assert events[0].user_id == "u1"
        assert events[0].enabled is False
