"""Shared pytest fixtures."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path

import pytest
from commit_reviewer.models import Commit, Evaluation, Rating

GitRepoFactory = Callable[[Sequence[str]], Path]


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def make_git_repo(tmp_path: Path) -> GitRepoFactory:
    """Return a factory that builds a hermetic git repo with the given messages.

    Commits are created oldest-first; ``git log`` therefore returns them
    newest-first (last message is the most recent commit).
    """

    counter = {"n": 0}

    def _factory(messages: Sequence[str]) -> Path:
        counter["n"] += 1
        repo = tmp_path / f"repo{counter['n']}"
        repo.mkdir()
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "user.name", "Test User")
        for index, message in enumerate(messages):
            (repo / f"file{index}.txt").write_text(f"content {index}\n")
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", message)
        return repo

    return _factory


@pytest.fixture
def sample_commits() -> list[Commit]:
    return [
        Commit(
            sha="aaaaaaa1111",
            author="Jane",
            date=datetime(2024, 1, 2),
            message="feat: add login flow",
        ),
        Commit(
            sha="bbbbbbb2222",
            author="John",
            date=datetime(2024, 1, 1),
            message="wip",
        ),
    ]


@pytest.fixture
def sample_evaluations() -> list[Evaluation]:
    return [
        Evaluation(rating=Rating.EXCELLENT, reasoning="Clear and descriptive."),
        Evaluation(rating=Rating.BAD, reasoning="Uninformative."),
    ]
