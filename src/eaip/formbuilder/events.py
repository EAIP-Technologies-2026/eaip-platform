"""Domain events for form builder service."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class FormCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.formbuilder.created"

    form_id: str
    name: str


class FormPublished(DomainEvent):
    event_type: ClassVar[str] = "eaip.formbuilder.published"

    form_id: str
    name: str


class FormSubmitted(DomainEvent):
    event_type: ClassVar[str] = "eaip.formbuilder.submitted"

    submission_id: str
    form_id: str
    submitted_by: str


class FormApproved(DomainEvent):
    event_type: ClassVar[str] = "eaip.formbuilder.approved"

    submission_id: str
    form_id: str
    approved_by: str


__all__ = [
    "FormApproved",
    "FormCreated",
    "FormPublished",
    "FormSubmitted",
]
