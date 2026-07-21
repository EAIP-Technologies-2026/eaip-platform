"""Tests for bluegreen exceptions."""

from __future__ import annotations

from eaip.bluegreen.exceptions import BlueGreenError, SwitchError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestBlueGreenError:
    def test_base_exception(self) -> None:
        err = BlueGreenError("Blue-green error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert str(err) == "Blue-green error"

    def test_with_context(self) -> None:
        err = BlueGreenError("Error", context={"env_id": "blue1"})
        assert err.context == {"env_id": "blue1"}


class TestSwitchError:
    def test_default_code(self) -> None:
        err = SwitchError("Switch failed")
        assert isinstance(err, BlueGreenError)
        assert err.code == ErrorCode.GATEWAY_ERROR

    def test_custom_message(self) -> None:
        err = SwitchError("Switch 'sw1' failed")
        assert "sw1" in str(err)
