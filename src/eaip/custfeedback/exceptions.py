"""Exception hierarchy for the customer feedback analyzer."""

from __future__ import annotations

from eaip.exceptions import EAIPError, ErrorCode


class FeedbackError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class FeedbackNotFoundError(FeedbackError):
    default_code = ErrorCode.NOT_FOUND
