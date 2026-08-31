"""Tests for Memory Engine exceptions."""

from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.memory.exceptions import (
    MemoryConsolidationError,
    MemoryEngineError,
    MemoryError,
    MemoryExpiredError,
    MemoryIndexingError,
    MemoryNotFoundError,
    MemoryRetrievalError,
    MemoryStoreError,
    MemorySummarizationError,
    MemoryValidationError,
)


class TestMemoryErrorBase:
    def test_is_exception(self) -> None:
        err = MemoryError("base error")
        assert isinstance(err, Exception)
        assert str(err) == "base error"

    def test_default_code(self) -> None:
        err = MemoryError("test")
        assert err.code is ErrorCode.UNKNOWN

    def test_with_context(self) -> None:
        err = MemoryError("test", context={"key": "val"})
        assert err.context["key"] == "val"


class TestMemoryNotFoundError:
    def test_default_code(self) -> None:
        err = MemoryNotFoundError("not found")
        assert err.code is ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        assert issubclass(MemoryNotFoundError, MemoryError)


class TestMemoryStoreError:
    def test_default_code(self) -> None:
        err = MemoryStoreError("store failed")
        assert err.code is ErrorCode.PROVIDER_UNAVAILABLE


class TestMemoryValidationError:
    def test_default_code(self) -> None:
        err = MemoryValidationError("validation failed")
        assert err.code is ErrorCode.VALIDATION_FAILED


class TestMemoryEngineError:
    def test_default_code(self) -> None:
        err = MemoryEngineError("engine error")
        assert err.code is ErrorCode.UNKNOWN

    def test_inheritance(self) -> None:
        assert issubclass(MemoryEngineError, MemoryError)


class TestMemoryIndexingError:
    def test_default_code(self) -> None:
        err = MemoryIndexingError("indexing failed")
        assert err.code is ErrorCode.UNKNOWN


class TestMemoryRetrievalError:
    def test_default_code(self) -> None:
        err = MemoryRetrievalError("retrieval failed")
        assert err.code is ErrorCode.UNKNOWN

    def test_inheritance(self) -> None:
        assert issubclass(MemoryRetrievalError, MemoryError)


class TestMemoryConsolidationError:
    def test_default_code(self) -> None:
        err = MemoryConsolidationError("consolidation failed")
        assert err.code is ErrorCode.UNKNOWN


class TestMemorySummarizationError:
    def test_default_code(self) -> None:
        err = MemorySummarizationError("summarization failed")
        assert err.code is ErrorCode.PROVIDER_UNAVAILABLE


class TestMemoryExpiredError:
    def test_default_code(self) -> None:
        err = MemoryExpiredError("expired")
        assert err.code is ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        assert issubclass(MemoryExpiredError, MemoryError)


class TestExceptionHierarchy:
    def test_all_subclass_memory_error(self) -> None:
        exceptions = [
            MemoryConsolidationError,
            MemoryEngineError,
            MemoryExpiredError,
            MemoryIndexingError,
            MemoryNotFoundError,
            MemoryRetrievalError,
            MemoryStoreError,
            MemorySummarizationError,
            MemoryValidationError,
        ]
        for exc in exceptions:
            assert issubclass(exc, MemoryError), f"{exc.__name__} does not subclass MemoryError"
