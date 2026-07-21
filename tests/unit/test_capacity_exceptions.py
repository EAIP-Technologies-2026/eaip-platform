"""Tests for capacity exceptions."""

from __future__ import annotations

from eaip.capacity.exceptions import CapacityError, ResourceNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestCapacityError:
    def test_base_exception(self) -> None:
        err = CapacityError("Capacity error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert str(err) == "Capacity error"

    def test_with_context(self) -> None:
        err = CapacityError("Error", context={"resource_id": "res1"})
        assert err.context == {"resource_id": "res1"}


class TestResourceNotFoundError:
    def test_default_code(self) -> None:
        err = ResourceNotFoundError("Resource not found")
        assert isinstance(err, CapacityError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = ResourceNotFoundError("Resource 'res1' not found")
        assert "res1" in str(err)
