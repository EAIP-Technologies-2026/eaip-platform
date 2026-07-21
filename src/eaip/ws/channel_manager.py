"""ChannelManager — create, update, delete channels and manage subscriptions."""

from __future__ import annotations

from typing import Any

from eaip.ws.exceptions import ChannelNotFoundError, SubscriptionError
from eaip.ws.models import Channel, Subscription


class ChannelManager:
    """Manages channels and user subscriptions."""

    def __init__(self) -> None:
        """Initialize the channel manager."""
        self._channels: dict[str, Channel] = {}
        self._subscriptions: dict[str, Subscription] = {}

    def create(self, channel: Channel) -> Channel:
        """Create a new channel."""
        self._channels[channel.id] = channel
        return channel

    def get(self, channel_id: str) -> Channel | None:
        """Get a channel by id, or None."""
        return self._channels.get(channel_id)

    def get_channel(self, channel_id: str) -> Channel:
        """Get a channel by id, raising if not found."""
        ch = self.get(channel_id)
        if ch is None:
            raise ChannelNotFoundError(
                f"Channel {channel_id!r} not found.",
                context={"channel_id": channel_id},
            )
        return ch

    def update(self, channel_id: str, **kwargs: Any) -> Channel:
        """Update fields on a channel."""
        existing = self.get_channel(channel_id)
        updated = existing.model_copy(update=kwargs)
        self._channels[channel_id] = updated
        return updated

    def delete(self, channel_id: str) -> Channel:
        """Delete a channel and its subscriptions."""
        ch = self._channels.pop(channel_id, None)
        if ch is None:
            raise ChannelNotFoundError(
                f"Channel {channel_id!r} not found.",
                context={"channel_id": channel_id},
            )
        self._subscriptions = {
            sid: sub for sid, sub in self._subscriptions.items() if sub.channel_id != channel_id
        }
        return ch

    def list_channels(self) -> list[Channel]:
        """Return all channels."""
        return list(self._channels.values())

    def subscribe(self, subscription: Subscription) -> Subscription:
        """Subscribe a user to a channel."""
        if subscription.channel_id not in self._channels:
            raise ChannelNotFoundError(
                f"Channel {subscription.channel_id!r} not found.",
                context={"channel_id": subscription.channel_id},
            )
        for existing in self._subscriptions.values():
            if (
                existing.channel_id == subscription.channel_id
                and existing.user_id == subscription.user_id
            ):
                raise SubscriptionError(
                    f"User {subscription.user_id!r} already subscribed to "
                    f"channel {subscription.channel_id!r}.",
                    context={
                        "user_id": subscription.user_id,
                        "channel_id": subscription.channel_id,
                    },
                )
        self._subscriptions[subscription.id] = subscription
        return subscription

    def unsubscribe(self, subscription_id: str) -> Subscription:
        """Unsubscribe a user from a channel."""
        sub = self._subscriptions.pop(subscription_id, None)
        if sub is None:
            raise SubscriptionError(
                f"Subscription {subscription_id!r} not found.",
                context={"subscription_id": subscription_id},
            )
        return sub

    def get_subscribers(self, channel_id: str) -> list[Subscription]:
        """Return all subscriptions for a channel."""
        return [sub for sub in self._subscriptions.values() if sub.channel_id == channel_id]

    def get_user_channels(self, user_id: str) -> list[Channel]:
        """Return all channels a user is subscribed to."""
        channel_ids = {
            sub.channel_id for sub in self._subscriptions.values() if sub.user_id == user_id
        }
        return [ch for ch in self._channels.values() if ch.id in channel_ids]

    def list_subscriptions(self) -> list[Subscription]:
        """Return all subscriptions."""
        return list(self._subscriptions.values())


__all__ = ["ChannelManager"]
