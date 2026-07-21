"""Form builder service — create, publish, submit, and approve forms."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from eaip.formbuilder.events import (
    FormApproved,
    FormCreated,
    FormPublished,
    FormSubmitted,
)
from eaip.formbuilder.exceptions import FormNotFoundError
from eaip.formbuilder.models import (
    FormConfig,
    FormDefinition,
    FormStatus,
    FormSubmission,
    SubmissionStatus,
)

EventCallback = Callable[[Any], Any]


class FormBuilderService:
    def __init__(
        self,
        config: FormConfig | None = None,
        event_callback: EventCallback | None = None,
    ) -> None:
        self._config = config or FormConfig()
        self._forms: dict[str, FormDefinition] = {}
        self._submissions: dict[str, FormSubmission] = {}
        self._event_callback = event_callback

    def set_event_callback(self, callback: EventCallback | None) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback:
            self._event_callback(event)

    # -- Form Definition CRUD ------------------------------------------------

    async def create_form(
        self,
        name: str,
        *,
        form_schema: dict[str, object] | None = None,
        fields: tuple[str, ...] | None = None,
        validation_rules: dict[str, object] | None = None,
        status: FormStatus = FormStatus.DRAFT,
    ) -> FormDefinition:
        form = FormDefinition(
            id=str(uuid.uuid4()),
            name=name,
            form_schema=form_schema or {},
            fields=fields or (),
            validation_rules=validation_rules or {},
            status=status,
        )
        self._forms[form.id] = form
        self._emit(FormCreated(form_id=form.id, name=name))
        return form

    async def get_form(self, form_id: str) -> FormDefinition:
        if form_id not in self._forms:
            raise FormNotFoundError(
                f"Form not found: {form_id}",
                context={"form_id": form_id},
            )
        return self._forms[form_id]

    async def list_forms(
        self,
        status: FormStatus | None = None,
    ) -> list[FormDefinition]:
        all_forms = list(self._forms.values())
        if status:
            all_forms = [f for f in all_forms if f.status == status]
        return all_forms

    async def publish_form(self, form_id: str) -> FormDefinition:
        form = await self.get_form(form_id)
        updated = FormDefinition(
            id=form.id,
            name=form.name,
            form_schema=form.form_schema,
            fields=form.fields,
            validation_rules=form.validation_rules,
            status=FormStatus.PUBLISHED,
        )
        self._forms[form_id] = updated
        self._emit(FormPublished(form_id=form_id, name=form.name))
        return updated

    async def archive_form(self, form_id: str) -> FormDefinition:
        form = await self.get_form(form_id)
        updated = FormDefinition(
            id=form.id,
            name=form.name,
            form_schema=form.form_schema,
            fields=form.fields,
            validation_rules=form.validation_rules,
            status=FormStatus.ARCHIVED,
        )
        self._forms[form_id] = updated
        return updated

    # -- Form Submission -----------------------------------------------------

    async def submit_form(
        self,
        form_id: str,
        data: dict[str, object],
        submitted_by: str,
    ) -> FormSubmission:
        form = await self.get_form(form_id)
        if form.status != FormStatus.PUBLISHED:
            raise RuntimeError(f"Form '{form.name}' is not published (status: {form.status.value})")

        submission = FormSubmission(
            id=str(uuid.uuid4()),
            form_id=form_id,
            data=data,
            submitted_by=submitted_by,
        )
        self._submissions[submission.id] = submission
        self._emit(
            FormSubmitted(
                submission_id=submission.id,
                form_id=form_id,
                submitted_by=submitted_by,
            )
        )
        return submission

    async def get_submission(self, submission_id: str) -> FormSubmission:
        if submission_id not in self._submissions:
            raise RuntimeError(f"Submission not found: {submission_id}")
        return self._submissions[submission_id]

    async def list_submissions(
        self,
        form_id: str | None = None,
        status: SubmissionStatus | None = None,
    ) -> list[FormSubmission]:
        result = list(self._submissions.values())
        if form_id:
            result = [s for s in result if s.form_id == form_id]
        if status:
            result = [s for s in result if s.status == status]
        return result

    async def approve_submission(
        self,
        submission_id: str,
        approved_by: str,
    ) -> FormSubmission:
        submission = await self.get_submission(submission_id)
        if submission.status != SubmissionStatus.PENDING:
            raise RuntimeError(f"Submission {submission_id} is not pending")

        updated = FormSubmission(
            id=submission.id,
            form_id=submission.form_id,
            data=submission.data,
            submitted_by=submission.submitted_by,
            submitted_at=submission.submitted_at,
            status=SubmissionStatus.APPROVED,
        )
        self._submissions[submission_id] = updated
        self._emit(
            FormApproved(
                submission_id=submission_id,
                form_id=submission.form_id,
                approved_by=approved_by,
            )
        )
        return updated

    async def reject_submission(
        self,
        submission_id: str,
    ) -> FormSubmission:
        submission = await self.get_submission(submission_id)
        if submission.status != SubmissionStatus.PENDING:
            raise RuntimeError(f"Submission {submission_id} is not pending")

        updated = FormSubmission(
            id=submission.id,
            form_id=submission.form_id,
            data=submission.data,
            submitted_by=submission.submitted_by,
            submitted_at=submission.submitted_at,
            status=SubmissionStatus.REJECTED,
        )
        self._submissions[submission_id] = updated
        return updated


__all__ = ["FormBuilderService"]
