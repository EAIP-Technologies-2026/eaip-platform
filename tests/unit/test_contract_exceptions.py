"""Tests for :mod:`eaip.contract.exceptions`."""

from __future__ import annotations

from eaip.contract.exceptions import ContractError, ContractNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestContractError:
    def test_base_exception(self) -> None:
        err = ContractError("contract failed")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert str(err) == "contract failed"


class TestContractNotFoundError:
    def test_default_code(self) -> None:
        err = ContractNotFoundError("contract not found")
        assert isinstance(err, ContractError)
        assert err.code == ErrorCode.NOT_FOUND

    def test_custom_message(self) -> None:
        err = ContractNotFoundError("Contract 'c1' not found")
        assert "c1" in str(err)
