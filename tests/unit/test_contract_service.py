"""Tests for :mod:`eaip.contract.manager`."""

from __future__ import annotations

from datetime import date

import pytest

from eaip.contract.exceptions import ContractError, ContractNotFoundError
from eaip.contract.manager import ContractManager
from eaip.contract.models import Contract, ContractConfig, ContractStatus, ContractVersion


class TestContractManager:
    @pytest.fixture
    def manager(self) -> ContractManager:
        return ContractManager()

    @pytest.fixture
    def sample_contract(self) -> Contract:
        return Contract(
            id="c1",
            title="Service Agreement",
            parties=("Acme Corp", "Beta LLC"),
            type="service",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )

    class TestCreateContract:
        async def test_create(self, manager: ContractManager, sample_contract: Contract) -> None:
            result = await manager.create_contract(sample_contract)
            assert result.id == "c1"
            assert result.title == "Service Agreement"

        async def test_list_contracts(
            self, manager: ContractManager, sample_contract: Contract
        ) -> None:
            await manager.create_contract(sample_contract)
            contracts = await manager.list_contracts()
            assert len(contracts) == 1

    class TestApprove:
        async def test_approve(self, manager: ContractManager, sample_contract: Contract) -> None:
            await manager.create_contract(sample_contract)
            result = await manager.approve("c1", "approver1")
            assert result.status == ContractStatus.ACTIVE

        async def test_approve_already_approved(
            self, manager: ContractManager, sample_contract: Contract
        ) -> None:
            await manager.create_contract(sample_contract)
            await manager.approve("c1", "approver1")
            with pytest.raises(ContractError):
                await manager.approve("c1", "approver2")

        async def test_approve_not_found(self, manager: ContractManager) -> None:
            with pytest.raises(ContractNotFoundError):
                await manager.approve("nonexistent", "approver1")

    class TestExpire:
        async def test_expire(self, manager: ContractManager, sample_contract: Contract) -> None:
            await manager.create_contract(sample_contract)
            result = await manager.expire("c1")
            assert result.status == ContractStatus.EXPIRED

        async def test_expire_not_found(self, manager: ContractManager) -> None:
            with pytest.raises(ContractNotFoundError):
                await manager.expire("nonexistent")

    class TestTerminate:
        async def test_terminate(self, manager: ContractManager, sample_contract: Contract) -> None:
            await manager.create_contract(sample_contract)
            result = await manager.terminate("c1", "breach of terms")
            assert result.status == ContractStatus.TERMINATED

        async def test_terminate_expired(
            self, manager: ContractManager, sample_contract: Contract
        ) -> None:
            await manager.create_contract(sample_contract)
            await manager.expire("c1")
            with pytest.raises(ContractError):
                await manager.terminate("c1", "already expired")

        async def test_terminate_not_found(self, manager: ContractManager) -> None:
            with pytest.raises(ContractNotFoundError):
                await manager.terminate("nonexistent", "reason")

    class TestVersion:
        async def test_add_version(
            self, manager: ContractManager, sample_contract: Contract
        ) -> None:
            await manager.create_contract(sample_contract)
            version = ContractVersion(
                id="v1",
                contract_id="c1",
                version=1,
                content="Contract terms...",
                change_summary="Initial version",
                created_by="user1",
            )
            result = await manager.add_version(version)
            assert result.version == 1

        async def test_get_versions(
            self, manager: ContractManager, sample_contract: Contract
        ) -> None:
            await manager.create_contract(sample_contract)
            v1 = ContractVersion(
                id="v1", contract_id="c1", version=1, content="v1", created_by="u1"
            )
            v2 = ContractVersion(
                id="v2", contract_id="c1", version=2, content="v2", created_by="u2"
            )
            await manager.add_version(v1)
            await manager.add_version(v2)
            versions = await manager.get_versions("c1")
            assert len(versions) == 2

    class TestGetContract:
        async def test_get(self, manager: ContractManager, sample_contract: Contract) -> None:
            await manager.create_contract(sample_contract)
            c = await manager.get_contract("c1")
            assert c.title == "Service Agreement"

        async def test_not_found(self, manager: ContractManager) -> None:
            with pytest.raises(ContractNotFoundError):
                await manager.get_contract("nonexistent")

    class TestConfig:
        def test_default_config(self) -> None:
            m = ContractManager()
            assert m.config.auto_archive_days == 365
            assert m.config.require_approval is True

        def test_custom_config(self) -> None:
            config = ContractConfig(auto_archive_days=180, require_approval=False)
            m = ContractManager(config=config)
            assert m.config.auto_archive_days == 180
            assert m.config.require_approval is False
