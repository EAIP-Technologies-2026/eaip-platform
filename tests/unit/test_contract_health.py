"""Tests for :mod:`eaip.contract.health`."""

from __future__ import annotations

import pytest

from eaip.contract.health import ContractHealthCheck


class TestContractHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy_with_contracts(self) -> None:
        check = ContractHealthCheck(contract_count=5, active_count=3)
        report = await check.check()
        assert report.component == "contract"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_degraded_no_contracts(self) -> None:
        check = ContractHealthCheck(contract_count=0, active_count=0)
        report = await check.check()
        assert report.status.value == "degraded"
        assert "No contracts registered" in report.message

    @pytest.mark.asyncio
    async def test_details(self) -> None:
        check = ContractHealthCheck(contract_count=10, active_count=4)
        report = await check.check()
        assert report.details["contract_count"] == 10
        assert report.details["active_count"] == 4
