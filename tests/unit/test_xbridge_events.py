"""Tests for :mod:`eaip.xbridge.events`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.xbridge.events import (
    ConnectorDeleted,
    ConnectorRegistered,
    ConnectorUpdated,
    MessageReceived,
    MessageSent,
)

ConnectorRegistered.__test__ = False
ConnectorUpdated.__test__ = False
ConnectorDeleted.__test__ = False
MessageSent.__test__ = False
MessageReceived.__test__ = False


class TestConnectorEvents:
    def test_registered(self) -> None:
        e = ConnectorRegistered(connector_id="c1", name="REST API", protocol="rest")
        assert e.event_type == "eaip.xbridge.connector.registered"
        assert e.connector_id == "c1"
        assert e.protocol == "rest"

    def test_updated(self) -> None:
        e = ConnectorUpdated(connector_id="c1", name="Updated API")
        assert e.event_type == "eaip.xbridge.connector.updated"
        assert e.name == "Updated API"

    def test_deleted(self) -> None:
        e = ConnectorDeleted(connector_id="c1", name="REST API")
        assert e.event_type == "eaip.xbridge.connector.deleted"
        assert e.connector_id == "c1"


class TestMessageEvents:
    def test_sent(self) -> None:
        e = MessageSent(message_id="m1", source="c1", target="c2", content_type="application/json")
        assert e.event_type == "eaip.xbridge.message.sent"
        assert e.source == "c1"
        assert e.target == "c2"

    def test_received(self) -> None:
        e = MessageReceived(
            message_id="m1", source="c1", target="c2", content_type="application/json"
        )
        assert e.event_type == "eaip.xbridge.message.received"
        assert e.message_id == "m1"


class TestEventImmutability:
    def test_registered_frozen(self) -> None:
        e = ConnectorRegistered(connector_id="c1", name="n", protocol="rest")
        with pytest.raises(ValidationError):
            e.connector_id = "changed"


class TestEventOccurredAt:
    def test_has_timestamp(self) -> None:
        e = ConnectorRegistered(connector_id="c1", name="n", protocol="rest")
        assert e.occurred_at is not None
