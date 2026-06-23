"""Typed domain models shared across the pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Rating(str, Enum):
    """LLM verdict on a single commit message."""

    EXCELLENT = "excellent"
    GOOD = "good"
    BAD = "bad"


class Mode(str, Enum):
    """How the target repository was sourced."""

    LOCAL = "local"
    REMOTE = "remote"


class Commit(BaseModel):
    """A single commit collected from a repository."""

    model_config = ConfigDict(frozen=True)

    sha: str
    author: str
    date: datetime
    message: str

    @property
    def short_sha(self) -> str:
        return self.sha[:7]

    @property
    def subject(self) -> str:
        """First line of the commit message."""
        return self.message.splitlines()[0] if self.message else ""


class Evaluation(BaseModel):
    """The LLM's structured verdict for a commit message."""

    model_config = ConfigDict(frozen=True)

    rating: Rating
    reasoning: str


class ReviewedCommit(BaseModel):
    """A commit paired with its evaluation, as shown in the report."""

    model_config = ConfigDict(frozen=True)

    sha: str
    author: str
    date: datetime
    message: str
    rating: Rating
    reasoning: str

    @classmethod
    def from_parts(cls, commit: Commit, evaluation: Evaluation) -> ReviewedCommit:
        return cls(
            sha=commit.sha,
            author=commit.author,
            date=commit.date,
            message=commit.message,
            rating=evaluation.rating,
            reasoning=evaluation.reasoning,
        )


class Summary(BaseModel):
    """Aggregate counts of ratings across the report."""

    model_config = ConfigDict(frozen=True)

    excellent: int = 0
    good: int = 0
    bad: int = 0

    @classmethod
    def from_commits(cls, commits: list[ReviewedCommit]) -> Summary:
        counts = {Rating.EXCELLENT: 0, Rating.GOOD: 0, Rating.BAD: 0}
        for commit in commits:
            counts[commit.rating] += 1
        return cls(
            excellent=counts[Rating.EXCELLENT],
            good=counts[Rating.GOOD],
            bad=counts[Rating.BAD],
        )


class Report(BaseModel):
    """The full report serialized to JSON for the frontend."""

    repo: str
    mode: Mode
    model: str
    generated_at: datetime = Field(default_factory=datetime.now)
    summary: Summary
    commits: list[ReviewedCommit]

    @classmethod
    def build(
        cls,
        *,
        repo: str,
        mode: Mode,
        model: str,
        commits: list[ReviewedCommit],
    ) -> Report:
        return cls(
            repo=repo,
            mode=mode,
            model=model,
            summary=Summary.from_commits(commits),
            commits=commits,
        )
