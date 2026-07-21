"""Tests for :mod:`eaip.envmgr.exceptions`."""

from __future__ import annotations

from eaip.envmgr.exceptions import EnvMgrError, VariableNotFoundError
from eaip.exceptions.base import ErrorCode


class TestEnvMgrError:
    def test_base_exception(self) -> None:
        err = EnvMgrError("manager error")
        assert str(err) == "manager error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestVariableNotFoundError:
    def test_default_code(self) -> None:
        err = VariableNotFoundError("not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = VariableNotFoundError("not found")
        assert isinstance(err, EnvMgrError)
