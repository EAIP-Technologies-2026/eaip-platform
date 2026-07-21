"""Tests for :mod:`eaip.extidmap.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.extidmap.exceptions import MappingError, MappingNotFoundError


class TestMappingError:
    def test_base_exception(self) -> None:
        err = MappingError("mapping error")
        assert str(err) == "mapping error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestMappingNotFoundError:
    def test_default_code(self) -> None:
        err = MappingNotFoundError("mapping not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = MappingNotFoundError("not found")
        assert isinstance(err, MappingError)
