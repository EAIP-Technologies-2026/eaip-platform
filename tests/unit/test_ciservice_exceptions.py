"""Tests for :mod:`eaip.ciservice.exceptions`."""

from __future__ import annotations

from eaip.ciservice.exceptions import BuildNotFoundError, CIError, PipelineNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestCIError:
    def test_base_exception(self) -> None:
        err = CIError("ci failed")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert str(err) == "ci failed"


class TestPipelineNotFoundError:
    def test_default_code(self) -> None:
        err = PipelineNotFoundError("pipeline not found")
        assert isinstance(err, CIError)
        assert err.code == ErrorCode.NOT_FOUND


class TestBuildNotFoundError:
    def test_default_code(self) -> None:
        err = BuildNotFoundError("build not found")
        assert isinstance(err, CIError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = BuildNotFoundError("Build 'b1' not found")
        assert "b1" in str(err)
