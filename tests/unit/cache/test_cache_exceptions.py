"""Tests for cache exception hierarchy."""

from __future__ import annotations

from eaip.cache.exceptions import CacheError, CacheMissError, CacheStorageError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestCacheError:
    def test_is_eaip_error(self) -> None:
        err = CacheError("generic error")
        assert isinstance(err, EAIPError)

    def test_default_code(self) -> None:
        err = CacheError("test")
        assert err.code == ErrorCode.UNKNOWN

    def test_message(self) -> None:
        err = CacheError("something went wrong")
        assert str(err) == "something went wrong"


class TestCacheMissError:
    def test_inherits_cache_error(self) -> None:
        err = CacheMissError("miss")
        assert isinstance(err, CacheError)

    def test_default_code(self) -> None:
        err = CacheMissError("not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_message(self) -> None:
        err = CacheMissError("key not found")
        assert str(err) == "key not found"


class TestCacheStorageError:
    def test_inherits_cache_error(self) -> None:
        err = CacheStorageError("storage fail")
        assert isinstance(err, CacheError)

    def test_default_code(self) -> None:
        err = CacheStorageError("oops")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_context(self) -> None:
        err = CacheStorageError("backend unavailable")
        assert err.context == {}
