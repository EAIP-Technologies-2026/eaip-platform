"""Domain events for the contract management service."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ContractCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.contract.created"
    contract_id: str
    title: str
    parties: tuple[str, ...]


class ContractApproved(DomainEvent):
    event_type: ClassVar[str] = "eaip.contract.approved"
    contract_id: str
    approved_by: str


class ContractExpired(DomainEvent):
    event_type: ClassVar[str] = "eaip.contract.expired"
    contract_id: str


class ContractTerminated(DomainEvent):
    event_type: ClassVar[str] = "eaip.contract.terminated"
    contract_id: str
    reason: str


__all__ = [
    "ContractApproved",
    "ContractCreated",
    "ContractExpired",
    "ContractTerminated",
]
