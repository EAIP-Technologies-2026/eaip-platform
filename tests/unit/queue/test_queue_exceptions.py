from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.queue.exceptions import QueueClosedError, QueueEmptyError, QueueError, QueueFullError


class TestQueueExceptions:
    def test_queue_error_base(self) -> None:
        err = QueueError("base")
        assert err.code == ErrorCode.UNKNOWN

    def test_queue_full_error(self) -> None:
        err = QueueFullError("full", context={"queue": "q"})
        assert err.code == ErrorCode.RATE_LIMITED

    def test_queue_empty_error(self) -> None:
        err = QueueEmptyError("empty", context={"queue": "q"})
        assert err.code == ErrorCode.NOT_FOUND

    def test_queue_closed_error(self) -> None:
        err = QueueClosedError("closed", context={"queue": "q"})
        assert err.code == ErrorCode.LIFECYCLE_FORBIDDEN

    def test_with_cause(self) -> None:
        cause = RuntimeError("root")
        err = QueueError("msg", cause=cause)
        assert err.__cause__ is cause

    def test_to_dict(self) -> None:
        err = QueueFullError("full", context={"queue": "q"})
        d = err.to_dict()
        assert d["type"] == "QueueFullError"

    def test_inheritance(self) -> None:
        assert issubclass(QueueFullError, QueueError)
        assert issubclass(QueueEmptyError, QueueError)
        assert issubclass(QueueClosedError, QueueError)
