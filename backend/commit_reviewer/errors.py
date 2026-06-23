"""Exception hierarchy for the commit reviewer."""

from __future__ import annotations


class CommitReviewerError(Exception):
    """Base class for all expected, user-facing errors."""


class CollectorError(CommitReviewerError):
    """Raised when commits cannot be collected from a repository."""


class EvaluatorError(CommitReviewerError):
    """Raised when the LLM evaluation cannot be performed (config or transport)."""
