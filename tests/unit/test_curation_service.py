"""Tests for :mod:`eaip.curation.curator`."""

from __future__ import annotations

import pytest

from eaip.curation.curator import CurationService
from eaip.curation.exceptions import CurationError, SubmissionNotFoundError
from eaip.curation.models import (
    ContentStatus,
    ContentSubmission,
    CurationConfig,
    CurationReview,
    QualityScore,
)


class TestCurationService:
    @pytest.fixture
    def service(self) -> CurationService:
        return CurationService()

    @pytest.fixture
    def sample_submission(self) -> ContentSubmission:
        return ContentSubmission(
            id="sub1",
            source="wiki",
            content="Some knowledge content",
            content_type="text",
            submitted_by="user1",
        )

    class TestSubmitContent:
        async def test_submit(
            self, service: CurationService, sample_submission: ContentSubmission
        ) -> None:
            result = await service.submit_content(sample_submission)
            assert result.id == "sub1"
            assert result.status == ContentStatus.PENDING

        async def test_list_submissions(
            self, service: CurationService, sample_submission: ContentSubmission
        ) -> None:
            await service.submit_content(sample_submission)
            submissions = await service.list_submissions()
            assert len(submissions) == 1

        async def test_list_by_status(
            self, service: CurationService, sample_submission: ContentSubmission
        ) -> None:
            await service.submit_content(sample_submission)
            pending = await service.list_submissions(status=ContentStatus.PENDING)
            approved = await service.list_submissions(status=ContentStatus.APPROVED)
            assert len(pending) == 1
            assert len(approved) == 0

    class TestGetSubmission:
        async def test_get(
            self, service: CurationService, sample_submission: ContentSubmission
        ) -> None:
            await service.submit_content(sample_submission)
            sub = await service.get_submission("sub1")
            assert sub.source == "wiki"

        async def test_not_found(self, service: CurationService) -> None:
            with pytest.raises(SubmissionNotFoundError):
                await service.get_submission("nonexistent")

    class TestReviewContent:
        async def test_review(
            self, service: CurationService, sample_submission: ContentSubmission
        ) -> None:
            await service.submit_content(sample_submission)
            score = QualityScore(
                submission_id="sub1",
                overall_score=0.9,
                relevance=0.8,
                accuracy=1.0,
                completeness=0.9,
                scored_by="reviewer1",
            )
            review = CurationReview(
                id="rev1",
                submission_id="sub1",
                reviewer="reviewer1",
                decision=ContentStatus.APPROVED,
                score=score,
            )
            result = await service.review_content(review)
            assert result.id == "rev1"
            assert result.decision == ContentStatus.APPROVED

    class TestApproveContent:
        async def test_approve(
            self, service: CurationService, sample_submission: ContentSubmission
        ) -> None:
            await service.submit_content(sample_submission)
            updated = await service.approve_content("sub1", "reviewer1")
            assert updated.status == ContentStatus.APPROVED

    class TestRejectContent:
        async def test_reject(
            self, service: CurationService, sample_submission: ContentSubmission
        ) -> None:
            await service.submit_content(sample_submission)
            updated = await service.reject_content("sub1", "reviewer1", "not relevant")
            assert updated.status == ContentStatus.REJECTED

    class TestFlagContent:
        async def test_flag(
            self, service: CurationService, sample_submission: ContentSubmission
        ) -> None:
            await service.submit_content(sample_submission)
            updated = await service.flag_content("sub1", "moderator", "inappropriate")
            assert updated.status == ContentStatus.FLAGGED

    class TestGetQualityScores:
        async def test_get_scores(
            self, service: CurationService, sample_submission: ContentSubmission
        ) -> None:
            await service.submit_content(sample_submission)
            score = QualityScore(
                submission_id="sub1",
                overall_score=0.85,
                relevance=0.8,
                accuracy=0.9,
                completeness=0.85,
                scored_by="auto",
            )
            review = CurationReview(
                id="rev1",
                submission_id="sub1",
                reviewer="auto",
                decision=ContentStatus.APPROVED,
                score=score,
            )
            await service.review_content(review)
            stored = await service.get_quality_scores("sub1")
            assert stored is not None
            assert stored.overall_score == 0.85

        async def test_no_scores(self, service: CurationService) -> None:
            score = await service.get_quality_scores("nonexistent")
            assert score is None

    class TestGetPendingReviews:
        async def test_get_pending(
            self, service: CurationService, sample_submission: ContentSubmission
        ) -> None:
            await service.submit_content(sample_submission)
            pending = await service.get_pending_reviews()
            assert len(pending) == 1

        async def test_no_pending(self, service: CurationService) -> None:
            pending = await service.get_pending_reviews()
            assert len(pending) == 0

    class TestConfig:
        def test_default_config(self) -> None:
            s = CurationService()
            assert s.config.auto_approve_threshold == 0.8
            assert s.config.require_review is True

        def test_custom_config(self) -> None:
            config = CurationConfig(auto_approve_threshold=0.9, require_review=False)
            s = CurationService(config=config)
            assert s.config.auto_approve_threshold == 0.9
            assert s.config.require_review is False
