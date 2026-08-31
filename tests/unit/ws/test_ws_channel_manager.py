from __future__ import annotations

import pytest

from eaip.ws.channel_manager import ChannelManager
from eaip.ws.exceptions import ChannelNotFoundError, SubscriptionError
from eaip.ws.models import Channel, Subscription


class TestChannelManager:
    def test_create(self) -> None:
        mgr = ChannelManager()
        ch = Channel(id="ch1", name="general")
        result = mgr.create(ch)
        assert result.id == "ch1"
        assert mgr.get("ch1") is ch

    def test_get_returns_none(self) -> None:
        mgr = ChannelManager()
        assert mgr.get("unknown") is None

    def test_get_channel(self) -> None:
        mgr = ChannelManager()
        ch = Channel(id="ch1", name="general")
        mgr.create(ch)
        assert mgr.get_channel("ch1") is ch

    def test_get_channel_not_found(self) -> None:
        mgr = ChannelManager()
        with pytest.raises(ChannelNotFoundError):
            mgr.get_channel("unknown")

    def test_update(self) -> None:
        mgr = ChannelManager()
        mgr.create(Channel(id="ch1", name="general"))
        updated = mgr.update("ch1", name="updated", description="new desc")
        assert updated.name == "updated"
        assert updated.description == "new desc"

    def test_update_not_found(self) -> None:
        mgr = ChannelManager()
        with pytest.raises(ChannelNotFoundError):
            mgr.update("unknown", name="x")

    def test_delete(self) -> None:
        mgr = ChannelManager()
        mgr.create(Channel(id="ch1", name="general"))
        result = mgr.delete("ch1")
        assert result.id == "ch1"
        assert mgr.get("ch1") is None

    def test_delete_not_found(self) -> None:
        mgr = ChannelManager()
        with pytest.raises(ChannelNotFoundError):
            mgr.delete("unknown")

    def test_list_channels_empty(self) -> None:
        mgr = ChannelManager()
        assert mgr.list_channels() == []

    def test_list_channels(self) -> None:
        mgr = ChannelManager()
        mgr.create(Channel(id="ch1", name="general"))
        mgr.create(Channel(id="ch2", name="random"))
        assert len(mgr.list_channels()) == 2

    def test_subscribe(self) -> None:
        mgr = ChannelManager()
        mgr.create(Channel(id="ch1", name="general"))
        sub = Subscription(id="s1", channel_id="ch1", user_id="u1")
        result = mgr.subscribe(sub)
        assert result.id == "s1"

    def test_subscribe_channel_not_found(self) -> None:
        mgr = ChannelManager()
        sub = Subscription(id="s1", channel_id="unknown", user_id="u1")
        with pytest.raises(ChannelNotFoundError):
            mgr.subscribe(sub)

    def test_subscribe_duplicate(self) -> None:
        mgr = ChannelManager()
        mgr.create(Channel(id="ch1", name="general"))
        mgr.subscribe(Subscription(id="s1", channel_id="ch1", user_id="u1"))
        with pytest.raises(SubscriptionError):
            mgr.subscribe(Subscription(id="s2", channel_id="ch1", user_id="u1"))

    def test_unsubscribe(self) -> None:
        mgr = ChannelManager()
        mgr.create(Channel(id="ch1", name="general"))
        mgr.subscribe(Subscription(id="s1", channel_id="ch1", user_id="u1"))
        result = mgr.unsubscribe("s1")
        assert result.id == "s1"

    def test_unsubscribe_not_found(self) -> None:
        mgr = ChannelManager()
        with pytest.raises(SubscriptionError):
            mgr.unsubscribe("unknown")

    def test_get_subscribers(self) -> None:
        mgr = ChannelManager()
        mgr.create(Channel(id="ch1", name="general"))
        mgr.subscribe(Subscription(id="s1", channel_id="ch1", user_id="u1"))
        mgr.subscribe(Subscription(id="s2", channel_id="ch1", user_id="u2"))
        subs = mgr.get_subscribers("ch1")
        assert len(subs) == 2

    def test_get_user_channels(self) -> None:
        mgr = ChannelManager()
        mgr.create(Channel(id="ch1", name="general"))
        mgr.create(Channel(id="ch2", name="random"))
        mgr.subscribe(Subscription(id="s1", channel_id="ch1", user_id="u1"))
        mgr.subscribe(Subscription(id="s2", channel_id="ch2", user_id="u1"))
        channels = mgr.get_user_channels("u1")
        assert len(channels) == 2

    def test_get_user_channels_empty(self) -> None:
        mgr = ChannelManager()
        assert mgr.get_user_channels("u1") == []

    def test_list_subscriptions(self) -> None:
        mgr = ChannelManager()
        mgr.create(Channel(id="ch1", name="general"))
        mgr.subscribe(Subscription(id="s1", channel_id="ch1", user_id="u1"))
        assert len(mgr.list_subscriptions()) == 1

    def test_delete_removes_subscriptions(self) -> None:
        mgr = ChannelManager()
        mgr.create(Channel(id="ch1", name="general"))
        mgr.subscribe(Subscription(id="s1", channel_id="ch1", user_id="u1"))
        mgr.delete("ch1")
        assert len(mgr.list_subscriptions()) == 0

    def test_get_subscribers_no_subs(self) -> None:
        mgr = ChannelManager()
        mgr.create(Channel(id="ch1", name="general"))
        assert mgr.get_subscribers("ch1") == []
