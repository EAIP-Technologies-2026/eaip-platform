from __future__ import annotations

import pydantic
import pytest

from eaip.ws.events import (
    ChannelCreated,
    ChannelDeleted,
    ClientConnected,
    ClientDisconnected,
    MessageBroadcast,
    MessagePublished,
    UserSubscribed,
    UserUnsubscribed,
    WsEvent,
)


class TestWsEvents:
    def test_ws_event_base(self) -> None:
        assert WsEvent.event_type == "eaip.ws.event"

    def test_client_connected(self) -> None:
        event = ClientConnected(
            connection_id="c1", user_id="u1", channel="ch1", metadata={"ip": "127.0.0.1"}
        )
        assert event.event_type == "eaip.ws.client.connected"
        assert event.connection_id == "c1"
        assert event.user_id == "u1"
        assert event.channel == "ch1"
        assert event.metadata["ip"] == "127.0.0.1"

    def test_client_disconnected(self) -> None:
        event = ClientDisconnected(
            connection_id="c1", user_id="u1", channel="ch1", reason="timeout"
        )
        assert event.event_type == "eaip.ws.client.disconnected"
        assert event.reason == "timeout"

    def test_client_disconnected_default_reason(self) -> None:
        event = ClientDisconnected(connection_id="c1", user_id="u1", channel="ch1")
        assert event.reason == ""

    def test_channel_created(self) -> None:
        event = ChannelCreated(channel_id="ch1", channel_name="general", channel_type="public")
        assert event.event_type == "eaip.ws.channel.created"
        assert event.channel_id == "ch1"
        assert event.channel_name == "general"
        assert event.channel_type == "public"

    def test_channel_deleted(self) -> None:
        event = ChannelDeleted(channel_id="ch1", channel_name="general")
        assert event.event_type == "eaip.ws.channel.deleted"
        assert event.channel_id == "ch1"

    def test_user_subscribed(self) -> None:
        event = UserSubscribed(user_id="u1", channel_id="ch1", subscription_id="s1")
        assert event.event_type == "eaip.ws.user.subscribed"
        assert event.user_id == "u1"
        assert event.channel_id == "ch1"

    def test_user_unsubscribed(self) -> None:
        event = UserUnsubscribed(user_id="u1", channel_id="ch1", subscription_id="s1")
        assert event.event_type == "eaip.ws.user.unsubscribed"

    def test_message_published(self) -> None:
        event = MessagePublished(
            message_id="m1", channel="ch1", event_type_name="chat", sender_id="u1"
        )
        assert event.event_type == "eaip.ws.message.published"
        assert event.message_id == "m1"
        assert event.channel == "ch1"

    def test_message_broadcast(self) -> None:
        event = MessageBroadcast(message_id="m1", sender_id="u1", except_channels=("ch2",))
        assert event.event_type == "eaip.ws.message.broadcast"
        assert event.except_channels == ("ch2",)

    def test_message_broadcast_default(self) -> None:
        event = MessageBroadcast(message_id="m1", sender_id="u1")
        assert event.except_channels == ()

    def test_frozen(self) -> None:
        event = ClientConnected(connection_id="c1", user_id="u1", channel="ch1")
        with pytest.raises(pydantic.ValidationError):
            event.connection_id = "c2"  # type: ignore[misc]
