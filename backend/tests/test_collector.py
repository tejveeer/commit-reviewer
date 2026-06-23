"""Tests for the commit collector.

    Each category below is delimited in the code with banner comments
    of the form  "CATEGORY: <name>" ... "end: <name>"  so the
    sections are easy to locate while scrolling.

    Log parsing
        _parse_log treated as a pure function over crafted delimited
        output: single and multiple commits, multiline bodies, unicode,
        empty input, plus malformed records and unparseable dates.

    Local collection
        collect_local against real, hermetic git repos built by the
        make_git_repo fixture: newest-first ordering, count limiting,
        and fewer commits than requested.

    Remote collection
        collect_remote against a file:// clone of a temp repo, so no
        network is touched.

    Error handling
        a missing path and a non-git directory both raise CollectorError.

    Dispatch
        collect routes to the remote path using an injected fake
        GitRunner, verifying behavior without invoking real git.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

import pytest
from commit_reviewer.collector import (
    _FIELD_SEP,
    _RECORD_SEP,
    CommitCollector,
    _parse_log,
)
from commit_reviewer.config import CliConfig
from commit_reviewer.errors import CollectorError
from commit_reviewer.models import Mode

GitRepoFactory = Callable[[Sequence[str]], Path]


def _record(sha: str, author: str, date: str, message: str) -> str:
    return f"{sha}{_FIELD_SEP}{author}{_FIELD_SEP}{date}{_FIELD_SEP}{message}{_RECORD_SEP}"


# ======================================================================
# CATEGORY: Log parsing
# ======================================================================


def test_parse_log_single_commit() -> None:
    output = _record("abc123", "Jane", "2024-01-01T00:00:00+00:00", "feat: x")
    commits = _parse_log(output)
    assert len(commits) == 1
    assert commits[0].sha == "abc123"
    assert commits[0].author == "Jane"
    assert commits[0].subject == "feat: x"


def test_parse_log_multiline_body_preserved() -> None:
    output = _record(
        "abc123", "Jane", "2024-01-01T00:00:00+00:00", "feat: x\n\nbody line 1\nbody line 2"
    )
    commits = _parse_log(output)
    assert commits[0].subject == "feat: x"
    assert "body line 1\nbody line 2" in commits[0].message


def test_parse_log_unicode() -> None:
    output = _record("abc123", "Jöhn Doe", "2024-01-01T00:00:00+00:00", "fix: café ☕")
    commits = _parse_log(output)
    assert commits[0].author == "Jöhn Doe"
    assert "café ☕" in commits[0].message


def test_parse_log_multiple_commits() -> None:
    output = _record("a", "A", "2024-01-02T00:00:00+00:00", "second") + "\n" + _record(
        "b", "B", "2024-01-01T00:00:00+00:00", "first"
    )
    commits = _parse_log(output)
    assert [c.sha for c in commits] == ["a", "b"]


def test_parse_log_empty_output() -> None:
    assert _parse_log("") == []


def test_parse_log_malformed_record_raises() -> None:
    bad = f"only{_FIELD_SEP}three{_FIELD_SEP}fields{_RECORD_SEP}"
    with pytest.raises(CollectorError, match="fields"):
        _parse_log(bad)


def test_parse_log_bad_date_raises() -> None:
    output = _record("abc", "Jane", "not-a-date", "feat: x")
    with pytest.raises(CollectorError, match="date"):
        _parse_log(output)


# end: Log parsing


# ======================================================================
# CATEGORY: Local collection
# ======================================================================


def test_collect_local_real_repo(make_git_repo: GitRepoFactory) -> None:
    repo = make_git_repo(["first", "second", "third"])
    commits = CommitCollector().collect_local(repo, count=10)
    assert [c.subject for c in commits] == ["third", "second", "first"]


def test_collect_local_respects_count(make_git_repo: GitRepoFactory) -> None:
    repo = make_git_repo(["a", "b", "c", "d"])
    commits = CommitCollector().collect_local(repo, count=2)
    assert [c.subject for c in commits] == ["d", "c"]


def test_collect_local_fewer_than_requested(make_git_repo: GitRepoFactory) -> None:
    repo = make_git_repo(["only one"])
    commits = CommitCollector().collect_local(repo, count=5)
    assert len(commits) == 1


# end: Local collection


# ======================================================================
# CATEGORY: Remote collection
# ======================================================================


def test_collect_remote_via_file_url(make_git_repo: GitRepoFactory) -> None:
    repo = make_git_repo(["first", "second"])
    url = f"file://{repo.resolve()}"
    commits = CommitCollector().collect_remote(url, count=10)
    assert {c.subject for c in commits} == {"first", "second"}


# end: Remote collection


# ======================================================================
# CATEGORY: Error handling
# ======================================================================


def test_collect_local_missing_path() -> None:
    with pytest.raises(CollectorError, match="does not exist"):
        CommitCollector().collect_local(Path("/no/such/path"), count=3)


def test_collect_local_not_a_repo(tmp_path: Path) -> None:
    with pytest.raises(CollectorError, match="Not a git repository"):
        CommitCollector().collect_local(tmp_path, count=3)


# end: Error handling


# ======================================================================
# CATEGORY: Dispatch
# ======================================================================


def test_collect_dispatches_remote_with_injected_runner() -> None:
    calls: list[list[str]] = []

    def fake_runner(args: list[str], cwd: Path | None = None) -> str:
        calls.append(args)
        if args[0] == "clone":
            return ""
        return _record("abc", "Jane", "2024-01-01T00:00:00+00:00", "feat: x")

    collector = CommitCollector(run_git=fake_runner)
    config = CliConfig(
        mode=Mode.REMOTE,
        target="https://example.com/x.git",
        count=3,
        port=3546,
        model="m",
        serve=False,
    )
    commits = collector.collect(config)
    assert commits[0].sha == "abc"
    assert any(c[0] == "clone" for c in calls)


# end: Dispatch
