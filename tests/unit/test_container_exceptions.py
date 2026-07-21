"""Tests for :mod:`eaip.container.exceptions`."""

from __future__ import annotations

from eaip.container.exceptions import ContainerError, ContainerNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestContainerError:
    def test_base_exception(self) -> None:
        err = ContainerError("container failed")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert str(err) == "container failed"


class TestContainerNotFoundError:
    def test_default_code(self) -> None:
        err = ContainerNotFoundError("not found")
        assert isinstance(err, ContainerError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = ContainerNotFoundError("Container 'c1' not found")
        assert "c1" in str(err)
