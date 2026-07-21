"""Tests for :mod:`eaip.sdk.events`."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.events.event import DomainEvent
from eaip.sdk.events import (
    ClientCreated,
    ClientExpired,
    ClientRevoked,
    SdkBuildCompleted,
    SdkBuildFailed,
    SdkBuildStarted,
    SdkCreated,
    SdkDeprecated,
    SdkPublished,
)


class TestSdkEvents:
    def test_sdk_created(self) -> None:
        event = SdkCreated(sdk_id="sdk-1", name="MySDK", language="python", version="1.0.0")
        assert event.event_type == "eaip.sdk.created"
        assert isinstance(event, DomainEvent)
        assert event.sdk_id == "sdk-1"
        assert event.name == "MySDK"

    def test_sdk_published(self) -> None:
        event = SdkPublished(sdk_id="sdk-1", version="1.0.0")
        assert event.event_type == "eaip.sdk.published"
        assert event.sdk_id == "sdk-1"

    def test_sdk_deprecated(self) -> None:
        event = SdkDeprecated(sdk_id="sdk-1", version="1.0.0")
        assert event.event_type == "eaip.sdk.deprecated"

    def test_sdk_build_started(self) -> None:
        event = SdkBuildStarted(build_id="bld-1", sdk_id="sdk-1", version="1.0.0")
        assert event.event_type == "eaip.sdk.build_started"
        assert event.build_id == "bld-1"

    def test_sdk_build_completed(self) -> None:
        event = SdkBuildCompleted(
            build_id="bld-1",
            sdk_id="sdk-1",
            version="1.0.0",
            duration_ms=1500,
            artifact_url="https://example.com/sdk.tar.gz",
        )
        assert event.event_type == "eaip.sdk.build_completed"
        assert event.duration_ms == 1500
        assert event.artifact_url == "https://example.com/sdk.tar.gz"

    def test_sdk_build_failed(self) -> None:
        event = SdkBuildFailed(
            build_id="bld-1",
            sdk_id="sdk-1",
            version="1.0.0",
            error="Compilation error",
        )
        assert event.event_type == "eaip.sdk.build_failed"
        assert event.error == "Compilation error"

    def test_client_created(self) -> None:
        event = ClientCreated(client_id="cli-1", sdk_id="sdk-1", name="MyApp")
        assert event.event_type == "eaip.sdk.client_created"
        assert event.client_id == "cli-1"
        assert event.name == "MyApp"

    def test_client_revoked(self) -> None:
        event = ClientRevoked(client_id="cli-1", sdk_id="sdk-1")
        assert event.event_type == "eaip.sdk.client_revoked"

    def test_client_expired(self) -> None:
        event = ClientExpired(client_id="cli-1", sdk_id="sdk-1")
        assert event.event_type == "eaip.sdk.client_expired"

    def test_events_are_frozen(self) -> None:
        event = SdkCreated(sdk_id="sdk-1", name="Test", language="py", version="1")
        with pytest.raises(ValueError):
            event.sdk_id = "other"  # type: ignore[misc]

    def test_events_have_occurred_at(self) -> None:
        event = SdkCreated(sdk_id="sdk-1", name="Test", language="py", version="1")
        assert isinstance(event.occurred_at, datetime)
