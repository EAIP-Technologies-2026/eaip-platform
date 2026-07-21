"""Tests for :mod:`eaip.devplatform.events`."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.devplatform.events import (
    ApiVersionDeprecated,
    ApiVersionRegistered,
    ApiVersionSunset,
    DeveloperKeyCreated,
    DeveloperKeyExpired,
    DeveloperKeyRevoked,
    PlaygroundSessionCreated,
    UsageRecorded,
)
from eaip.events.event import DomainEvent


class TestDevPlatformEvents:
    def test_api_version_registered(self) -> None:
        event = ApiVersionRegistered(version_id="v1", version_string="1.0.0")
        assert event.event_type == "eaip.devplatform.api_version_registered"
        assert isinstance(event, DomainEvent)
        assert event.version_id == "v1"
        assert event.version_string == "1.0.0"

    def test_api_version_deprecated(self) -> None:
        event = ApiVersionDeprecated(version_id="v1", version_string="1.0.0")
        assert event.event_type == "eaip.devplatform.api_version_deprecated"
        assert event.version_id == "v1"

    def test_api_version_deprecated_with_sunset(self) -> None:
        dt = datetime(2026, 1, 1)
        event = ApiVersionDeprecated(version_id="v1", version_string="1.0.0", sunset_at=dt)
        assert event.sunset_at == dt

    def test_api_version_sunset(self) -> None:
        event = ApiVersionSunset(version_id="v1", version_string="1.0.0")
        assert event.event_type == "eaip.devplatform.api_version_sunset"
        assert event.version_string == "1.0.0"

    def test_developer_key_created(self) -> None:
        event = DeveloperKeyCreated(key_id="k1", developer_id="d1", name="My Key")
        assert event.event_type == "eaip.devplatform.developer_key_created"
        assert event.key_id == "k1"
        assert event.name == "My Key"

    def test_developer_key_revoked(self) -> None:
        event = DeveloperKeyRevoked(key_id="k1", developer_id="d1")
        assert event.event_type == "eaip.devplatform.developer_key_revoked"
        assert event.developer_id == "d1"

    def test_developer_key_expired(self) -> None:
        event = DeveloperKeyExpired(key_id="k1", developer_id="d1")
        assert event.event_type == "eaip.devplatform.developer_key_expired"

    def test_usage_recorded(self) -> None:
        event = UsageRecorded(
            record_id="r1",
            developer_id="d1",
            api_version="1.0.0",
            endpoint="/users",
            status_code=200,
            response_time_ms=150.5,
        )
        assert event.event_type == "eaip.devplatform.usage_recorded"
        assert event.status_code == 200
        assert event.response_time_ms == 150.5

    def test_playground_session_created(self) -> None:
        event = PlaygroundSessionCreated(session_id="s1", developer_id="d1", endpoint_id="e1")
        assert event.event_type == "eaip.devplatform.playground_session_created"
        assert event.session_id == "s1"

    def test_all_events_are_frozen(self) -> None:
        event = ApiVersionRegistered(version_id="v1", version_string="1.0.0")
        with pytest.raises(ValueError):
            event.version_id = "changed"  # type: ignore[misc]

    def test_all_have_occurred_at(self) -> None:
        event = DeveloperKeyCreated(key_id="k1", developer_id="d1", name="Test")
        assert isinstance(event.occurred_at, datetime)
