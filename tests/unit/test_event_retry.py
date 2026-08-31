"""Tests for retry strategies."""

from __future__ import annotations

import pytest

from eaip.events.envelope import EventEnvelope
from eaip.events.event import DomainEvent
from eaip.events.retry import (
    ExponentialBackoffRetry,
    FixedDelayRetry,
    ImmediateRetry,
)


class DummyEvent(DomainEvent):
    event_type = "dummy"


@pytest.fixture
def envelope():
    return EventEnvelope.from_event(DummyEvent())


class TestImmediateRetry:
    async def test_retry_up_to_max(self, envelope):
        strategy = ImmediateRetry(max_retries=3)
        exc = ValueError("fail")

        assert await strategy.should_retry(envelope, exc, 0) == 0.0
        assert await strategy.should_retry(envelope, exc, 1) == 0.0
        assert await strategy.should_retry(envelope, exc, 2) == 0.0
        assert await strategy.should_retry(envelope, exc, 3) is None

    async def test_zero_max_no_retries(self, envelope):
        strategy = ImmediateRetry(max_retries=0)

        assert await strategy.should_retry(envelope, ValueError(), 0) is None


class TestFixedDelayRetry:
    async def test_fixed_delay(self, envelope):
        strategy = FixedDelayRetry(delay=2.0, max_retries=2)

        assert await strategy.should_retry(envelope, ValueError(), 0) == 2.0
        assert await strategy.should_retry(envelope, ValueError(), 1) == 2.0
        assert await strategy.should_retry(envelope, ValueError(), 2) is None


class TestExponentialBackoffRetry:
    async def test_exponential_delay(self, envelope):
        strategy = ExponentialBackoffRetry(
            base_delay=1.0,
            max_retries=3,
            jitter=False,
        )

        d0 = await strategy.should_retry(envelope, ValueError(), 0)
        d1 = await strategy.should_retry(envelope, ValueError(), 1)
        d2 = await strategy.should_retry(envelope, ValueError(), 2)
        d3 = await strategy.should_retry(envelope, ValueError(), 3)

        assert d0 == 1.0
        assert d1 == 2.0
        assert d2 == 4.0
        assert d3 is None

    async def test_respects_max_delay(self, envelope):
        strategy = ExponentialBackoffRetry(
            base_delay=10.0,
            max_retries=5,
            max_delay=15.0,
            jitter=False,
        )

        d0 = await strategy.should_retry(envelope, ValueError(), 0)
        d1 = await strategy.should_retry(envelope, ValueError(), 1)
        d2 = await strategy.should_retry(envelope, ValueError(), 2)

        assert d0 == 10.0
        assert d1 == 15.0  # capped
        assert d2 == 15.0  # capped

    async def test_jitter_adds_variance(self, envelope):
        strategy = ExponentialBackoffRetry(
            base_delay=10.0,
            max_retries=3,
            jitter=True,
        )

        delays = []
        for _ in range(20):
            d = await strategy.should_retry(envelope, ValueError(), 0)
            delays.append(d)

        # All should be >= base_delay with jitter
        assert all(d >= 10.0 for d in delays)
        # Not all identical (jitter adds randomness)
        assert len(set(delays)) > 1
