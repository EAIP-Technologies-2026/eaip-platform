"""Tests for cacheinv exceptions."""

from __future__ import annotations

from eaip.cacheinv.exceptions import InvalidationError, TagNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestInvalidationError:
    def test_base_exception(self) -> None:
        err = InvalidationError("Invalidation error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.CACHE_ERROR
        assert str(err) == "Invalidation error"

    def test_with_context(self) -> None:
        err = InvalidationError("Error", context={"tag_id": "t1"})
        assert err.context == {"tag_id": "t1"}


class TestTagNotFoundError:
    def test_default_code(self) -> None:
        err = TagNotFoundError("Tag not found")
        assert isinstance(err, InvalidationError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = TagNotFoundError("Tag 'xyz' not found")
        assert "xyz" in str(err)
