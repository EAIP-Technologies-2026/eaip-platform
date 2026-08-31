"""CurationService — submit, review, approve, reject, and flag knowledge content."""

from __future__ import annotations

from eaip.curation.events import (
    ContentApproved,
    ContentFlagged,
    ContentRejected,
    ContentSubmitted,
)
from eaip.curation.exceptions import (
    SubmissionNotFoundError,
)
from eaip.curation.models import (
    ContentStatus,
    ContentSubmission,
    CurationConfig,
    CurationReview,
    QualityScore,
)
from eaip.logging.context import get_logger


class CurationService:
    """Central service for curating knowledge content."""

    def __init__(self, config: CurationConfig | None = None) -> None:
        self._config = config or CurationConfig()
        self._submissions: dict[str, ContentSubmission] = {}
        self._reviews: dict[str, CurationReview] = {}
        self._quality_scores: dict[str, QualityScore] = {}
        self._log = get_logger("eaip.curation.curator")

    @property
    def config(self) -> CurationConfig:
        return self._config

    async def submit_content(self, submission: ContentSubmission) -> ContentSubmission:
        """Submit new content for curation."""
        self._submissions[submission.id] = submission
        event = ContentSubmitted(
            submission_id=submission.id,
            source=submission.source,
            content_type=submission.content_type,
            submitted_by=submission.submitted_by,
        )
        self._log.info("curation.content.submitted", submission_id=submission.id)
        return submission

    async def get_submission(self, submission_id: str) -> ContentSubmission:
        """Retrieve a content submission by ID."""
        submission = self._submissions.get(submission_id)
        if submission is None:
            raise SubmissionNotFoundError(f"Submission '{submission_id}' not found")
        return submission

    async def list_submissions(
        self, status: ContentStatus | None = None
    ) -> list[ContentSubmission]:
        """List content submissions, optionally filtered by status."""
        submissions = list(self._submissions.values())
        if status is not None:
            submissions = [s for s in submissions if s.status == status]
        return sorted(submissions, key=lambda s: s.submitted_at, reverse=True)

    async def review_content(self, review: CurationReview) -> CurationReview:
        """Record a review for a content submission."""
        submission = await self.get_submission(review.submission_id)
        self._reviews[review.id] = review
        if review.score is not None:
            self._quality_scores[review.submission_id] = review.score
        self._log.info(
            "curation.content.reviewed",
            submission_id=review.submission_id,
            reviewer=review.reviewer,
        )
        return review

    async def approve_content(
        self, submission_id: str, reviewer: str, comments: str = ""
    ) -> ContentSubmission:
        """Approve a content submission."""
        submission = await self.get_submission(submission_id)
        updated = submission.model_copy(update={"status": ContentStatus.APPROVED}, deep=True)
        self._submissions[submission_id] = updated

        score = self._quality_scores.get(submission_id)
        event = ContentApproved(
            submission_id=submission_id,
            reviewer=reviewer,
            score=score.overall_score if score else None,
        )
        self._log.info("curation.content.approved", submission_id=submission_id, reviewer=reviewer)
        return updated

    async def reject_content(
        self, submission_id: str, reviewer: str, reason: str = ""
    ) -> ContentSubmission:
        """Reject a content submission."""
        submission = await self.get_submission(submission_id)
        updated = submission.model_copy(update={"status": ContentStatus.REJECTED}, deep=True)
        self._submissions[submission_id] = updated
        event = ContentRejected(
            submission_id=submission_id,
            reviewer=reviewer,
            reason=reason or "Rejected by reviewer",
        )
        self._log.info("curation.content.rejected", submission_id=submission_id, reviewer=reviewer)
        return updated

    async def flag_content(
        self, submission_id: str, flagged_by: str, reason: str = ""
    ) -> ContentSubmission:
        """Flag a content submission for further review."""
        submission = await self.get_submission(submission_id)
        updated = submission.model_copy(update={"status": ContentStatus.FLAGGED}, deep=True)
        self._submissions[submission_id] = updated
        event = ContentFlagged(
            submission_id=submission_id,
            flagged_by=flagged_by,
            reason=reason or "Flagged for review",
        )
        self._log.info(
            "curation.content.flagged", submission_id=submission_id, flagged_by=flagged_by
        )
        return updated

    async def get_quality_scores(self, submission_id: str) -> QualityScore | None:
        """Get the quality score for a submission."""
        return self._quality_scores.get(submission_id)

    async def get_pending_reviews(self) -> list[ContentSubmission]:
        """Get all submissions pending review."""
        return [s for s in self._submissions.values() if s.status == ContentStatus.PENDING]


__all__ = ["CurationService"]
