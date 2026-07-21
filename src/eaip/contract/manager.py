"""ContractManager — central service for managing contracts and their lifecycle."""

from __future__ import annotations

from eaip.contract.events import (
    ContractApproved,
    ContractCreated,
    ContractExpired,
    ContractTerminated,
)
from eaip.contract.exceptions import ContractError, ContractNotFoundError
from eaip.contract.models import (
    Contract,
    ContractConfig,
    ContractStatus,
    ContractVersion,
)
from eaip.logging.context import get_logger


class ContractManager:
    def __init__(self, config: ContractConfig | None = None) -> None:
        self._config = config or ContractConfig()
        self._contracts: dict[str, Contract] = {}
        self._versions: dict[str, ContractVersion] = {}
        self._log = get_logger("eaip.contract.manager")

    @property
    def config(self) -> ContractConfig:
        return self._config

    async def create_contract(self, contract: Contract) -> Contract:
        self._contracts[contract.id] = contract
        event = ContractCreated(
            contract_id=contract.id,
            title=contract.title,
            parties=contract.parties,
        )
        self._log.info("contract.created", contract_id=contract.id, title=contract.title)
        return contract

    async def approve(self, contract_id: str, approved_by: str) -> Contract:
        contract = self._get_contract(contract_id)
        if contract.status != ContractStatus.DRAFT:
            raise ContractError(
                f"Cannot approve contract '{contract_id}' in status {contract.status}"
            )
        updated = Contract(
            id=contract.id,
            title=contract.title,
            parties=contract.parties,
            type=contract.type,
            status=ContractStatus.ACTIVE,
            start_date=contract.start_date,
            end_date=contract.end_date,
            terms=contract.terms,
            value=contract.value,
            metadata=contract.metadata,
        )
        self._contracts[contract_id] = updated
        event = ContractApproved(contract_id=contract_id, approved_by=approved_by)
        self._log.info("contract.approved", contract_id=contract_id)
        return updated

    async def expire(self, contract_id: str) -> Contract:
        contract = self._get_contract(contract_id)
        updated = Contract(
            id=contract.id,
            title=contract.title,
            parties=contract.parties,
            type=contract.type,
            status=ContractStatus.EXPIRED,
            start_date=contract.start_date,
            end_date=contract.end_date,
            terms=contract.terms,
            value=contract.value,
            metadata=contract.metadata,
        )
        self._contracts[contract_id] = updated
        event = ContractExpired(contract_id=contract_id)
        self._log.info("contract.expired", contract_id=contract_id)
        return updated

    async def terminate(self, contract_id: str, reason: str) -> Contract:
        contract = self._get_contract(contract_id)
        if contract.status in (ContractStatus.EXPIRED, ContractStatus.TERMINATED):
            raise ContractError(
                f"Cannot terminate contract '{contract_id}' in status {contract.status}"
            )
        updated = Contract(
            id=contract.id,
            title=contract.title,
            parties=contract.parties,
            type=contract.type,
            status=ContractStatus.TERMINATED,
            start_date=contract.start_date,
            end_date=contract.end_date,
            terms=contract.terms,
            value=contract.value,
            metadata=contract.metadata,
        )
        self._contracts[contract_id] = updated
        event = ContractTerminated(contract_id=contract_id, reason=reason)
        self._log.info("contract.terminated", contract_id=contract_id)
        return updated

    async def add_version(self, version: ContractVersion) -> ContractVersion:
        self._versions[version.id] = version
        self._log.info(
            "contract.version.added", contract_id=version.contract_id, version=version.version
        )
        return version

    async def get_contract(self, contract_id: str) -> Contract:
        return self._get_contract(contract_id)

    async def list_contracts(self) -> list[Contract]:
        return list(self._contracts.values())

    async def get_versions(self, contract_id: str) -> list[ContractVersion]:
        return [v for v in self._versions.values() if v.contract_id == contract_id]

    def _get_contract(self, contract_id: str) -> Contract:
        contract = self._contracts.get(contract_id)
        if contract is None:
            raise ContractNotFoundError(f"Contract '{contract_id}' not found")
        return contract
