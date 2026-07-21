"""Tests for modelmon exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.modelmon.exceptions import ModelMonitorError, ModelNotFoundError


class TestModelMonitorError:
    def test_base_exception(self) -> None:
        err = ModelMonitorError("Something went wrong")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert str(err) == "Something went wrong"

    def test_with_context(self) -> None:
        err = ModelMonitorError("Error", context={"model_id": "m1"})
        assert err.context == {"model_id": "m1"}


class TestModelNotFoundError:
    def test_default_code(self) -> None:
        err = ModelNotFoundError("Model not found")
        assert isinstance(err, ModelMonitorError)
        assert err.code == ErrorCode.MODEL_NOT_FOUND
        assert str(err) == "Model not found"

    def test_custom_message(self) -> None:
        err = ModelNotFoundError("Model 'xyz' not found in monitor")
        assert "xyz" in str(err)
