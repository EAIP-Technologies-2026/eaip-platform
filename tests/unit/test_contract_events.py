"""Tests for :mod:`eaip.contract.events`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.contract.events import (
    ContractApproved,
    ContractCreated,
    ContractExpired,
    ContractTerminated,
)
from eaip.events.event import DomainEvent


class TestContractCreated:
    def test_event_type(self) -> None:
        event = ContractCreated(
            contract_id="c1", title="Service Agreement", parties=("PartyA", "PartyB")
        )
        assert event.event_type == "eaip.contract.created"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = ContractCreated(
            contract_id="c1", title="Service Agreement", parties=("PartyA", "PartyB")
        )
        assert event.contract_id == "c1"
        assert event.title == "Service Agreement"
        assert event.parties == ("PartyA", "PartyB")


class TestContractApproved:
    def test_event_type(self) -> None:
        event = ContractApproved(contract_id="c1", approved_by="approver1")
        assert event.event_type == "eaip.contract.approved"

    def test_fields(self) -> None:
        event = ContractApproved(contract_id="c1", approved_by="approver1")
        assert event.approved_by == "approver1"


class TestContractExpired:
    def test_event_type(self) -> None:
        event = ContractExpired(contract_id="c1")
        assert event.event_type == "eaip.contract.expired"


class TestContractTerminated:
    def test_event_type(self) -> None:
        event = ContractTerminated(contract_id="c1", reason="breach of terms")
        assert event.event_type == "eaip.contract.terminated"


class TestEventImmutability:
    def test_frozen(self) -> None:
        event = ContractCreated(contract_id="c1", title="Agreement", parties=("A", "B"))
        with pytest.raises(ValidationError):
            event.contract_id = "changed"


class TestEventOccurredAt:
    def test_has_timestamp(self) -> None:
        event = ContractCreated(contract_id="c1", title="Agreement", parties=("A", "B"))
        assert event.occurred_at is not None
