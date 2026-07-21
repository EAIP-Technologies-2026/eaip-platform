from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.searchidx.exceptions import (
    CacheError,
    CacheNotFoundError,
    IndexBuildError,
    IndexNotFoundError,
    SearchIndexError,
)


class TestSearchidxExceptions:
    def test_search_index_error(self) -> None:
        err = SearchIndexError("base")
        assert err.code == ErrorCode.UNKNOWN

    def test_index_not_found(self) -> None:
        err = IndexNotFoundError("missing", context={"index_id": "idx1"})
        assert err.code == ErrorCode.NOT_FOUND
        assert err.context["index_id"] == "idx1"

    def test_index_build_error(self) -> None:
        err = IndexBuildError("build failed", context={"index_id": "idx1"})
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_cache_error(self) -> None:
        err = CacheError("cache error")
        assert err.code == ErrorCode.CACHE_ERROR

    def test_cache_not_found(self) -> None:
        err = CacheNotFoundError("key not found", context={"key": "mykey"})
        assert err.code == ErrorCode.NOT_FOUND

    def test_with_cause(self) -> None:
        cause = RuntimeError("root")
        err = SearchIndexError("msg", cause=cause)
        assert err.__cause__ is cause

    def test_to_dict(self) -> None:
        err = IndexNotFoundError("missing", context={"index_id": "idx1"})
        d = err.to_dict()
        assert d["type"] == "IndexNotFoundError"
        assert d["code"] == "EAIP-0003"
        assert d["context"]["index_id"] == "idx1"

    def test_inheritance(self) -> None:
        assert issubclass(IndexNotFoundError, SearchIndexError)
        assert issubclass(IndexBuildError, SearchIndexError)
        assert issubclass(CacheError, SearchIndexError)
        assert issubclass(CacheNotFoundError, CacheError)
