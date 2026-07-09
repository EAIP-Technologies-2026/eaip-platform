"""Retry strategies for event handler execution."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eaip.events.envelope import EventEnvelope


class RetryStrategy(ABC):
    """Abstract base for retry strategies."""

    @abstractmethod
    async def should_retry(
        self,
        envelope: EventEnvelope,
        exception: BaseException,
        attempt: int,
    ) -> float | None:
        """Decide whether to retry after a failed handler invocation.

        Args:
            envelope: The event envelope that was being delivered.
            exception: The exception raised by the handler.
            attempt: The attempt number (0-based).

        Returns:
            Delay in seconds before the next retry, or ``None`` to give up.
        """
        ...


@dataclass
class ImmediateRetry(RetryStrategy):
    """Retry immediately up to ``max_retries`` times with no delay."""

    max_retries: int = 3

    async def should_retry(
        self,
        _envelope: EventEnvelope,
        _exception: BaseException,
        attempt: int,
    ) -> float | None:
        """Retry immediately up to max_retries, then give up."""
        if attempt < self.max_retries:
            return 0.0
        return None


@dataclass
class FixedDelayRetry(RetryStrategy):
    """Retry with a fixed delay between attempts."""

    delay: float = 1.0
    max_retries: int = 3

    async def should_retry(
        self,
        _envelope: EventEnvelope,
        _exception: BaseException,
        attempt: int,
    ) -> float | None:
        """Retry with fixed delay up to max_retries, then give up."""
        if attempt < self.max_retries:
            return self.delay
        return None


@dataclass
class ExponentialBackoffRetry(RetryStrategy):
    """Retry with exponential backoff and optional jitter.

    Delay formula: ``base_delay * (2 ** attempt) + jitter``
    """

    base_delay: float = 1.0
    max_retries: int = 3
    max_delay: float = 60.0
    jitter: bool = True

    async def should_retry(
        self,
        _envelope: EventEnvelope,
        _exception: BaseException,
        attempt: int,
    ) -> float | None:
        """Retry with exponential delay up to max_retries, then give up."""
        if attempt >= self.max_retries:
            return None
        delay = self.base_delay * (2.0**attempt)
        if self.jitter:
            delay += random.uniform(0, delay * 0.1)  # noqa: S311
        return min(delay, self.max_delay)


__all__ = [
    "ExponentialBackoffRetry",
    "FixedDelayRetry",
    "ImmediateRetry",
    "RetryStrategy",
]
