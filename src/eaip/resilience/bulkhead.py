"""Bulkhead pattern for isolating failures and limiting concurrent execution."""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel, ConfigDict

from eaip.logging.context import get_logger


class BulkheadConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_concurrent: int = 10
    max_queue_size: int = 20
    queue_timeout_seconds: float = 30.0


class Bulkhead:
    """Bulkhead semaphore for limiting concurrent executions."""

    def __init__(
        self,
        name: str,
        config: BulkheadConfig | None = None,
        *,
        meter: Any = None,
    ) -> None:
        self._name = name
        self._config = config or BulkheadConfig()
        self._semaphore = asyncio.Semaphore(self._config.max_concurrent)
        self._queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=self._config.max_queue_size)
        self._active_count = 0
        self._queued_count = 0
        self._rejected_count = 0
        self._meter = meter
        self._log = get_logger(f"eaip.resilience.bulkhead.{name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def active_count(self) -> int:
        return self._active_count

    @property
    def queued_count(self) -> int:
        return self._queued_count

    @property
    def rejected_count(self) -> int:
        return self._rejected_count

    async def execute(
        self,
        coro_fn: Any,
        *args: Any,
        fallback: Any = None,
        **kwargs: Any,
    ) -> Any:
        if self._semaphore.locked() and self._queue.qsize() >= self._config.max_queue_size:
            self._rejected_count += 1
            self._log.warning("bulkhead.rejected", name=self._name)
            if fallback is not None:
                return fallback() if callable(fallback) else fallback
            raise BulkheadRejectedError(self._name)

        coro = coro_fn(*args, **kwargs) if callable(coro_fn) else coro_fn
        try:
            async with self._semaphore:
                self._active_count += 1
                try:
                    return await asyncio.wait_for(
                        coro,
                        timeout=self._config.queue_timeout_seconds,
                    )
                finally:
                    self._active_count -= 1
        except TimeoutError:
            self._log.warning("bulkhead.timeout", name=self._name)
            if fallback is not None:
                return fallback() if callable(fallback) else fallback
            raise BulkheadTimeoutError(self._name)

    def get_metrics(self) -> dict[str, object]:
        return {
            "name": self._name,
            "active_count": self._active_count,
            "queued_count": self._queued_count,
            "rejected_count": self._rejected_count,
            "max_concurrent": self._config.max_concurrent,
        }


class BulkheadRejectedError(Exception):
    def __init__(self, name: str) -> None:
        self.bulkhead_name = name
        super().__init__(f"bulkhead {name!r} rejected request (queue full)")


class BulkheadTimeoutError(Exception):
    def __init__(self, name: str) -> None:
        self.bulkhead_name = name
        super().__init__(f"bulkhead {name!r} timed out")


__all__ = [
    "Bulkhead",
    "BulkheadConfig",
    "BulkheadRejectedError",
    "BulkheadTimeoutError",
]
