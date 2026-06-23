"""Collect recent commits from local or remote git repositories."""

from __future__ import annotations

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Protocol

from .config import CliConfig
from .errors import CollectorError
from .models import Commit, Mode

#: Field separator (unit separator) and record separator (record separator) chosen
#: so that arbitrary multiline commit bodies never collide with our delimiters.
_FIELD_SEP = "\x1f"
_RECORD_SEP = "\x1e"
_LOG_FORMAT = f"--pretty=format:%H{_FIELD_SEP}%an{_FIELD_SEP}%aI{_FIELD_SEP}%B{_RECORD_SEP}"


class GitRunner(Protocol):
    """Callable that runs a git subcommand and returns its stdout."""

    def __call__(self, args: list[str], cwd: Path | None = None) -> str: ...


def _default_run_git(args: list[str], cwd: Path | None = None) -> str:
    """Run git with the given args, returning stdout or raising CollectorError."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError as exc:
        raise CollectorError(
            "git executable not found on PATH; please install git."
        ) from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown git error"
        raise CollectorError(f"git {' '.join(args)} failed: {stderr}")
    return result.stdout


def _parse_log(output: str) -> list[Commit]:
    """Parse delimited git log output into typed commits (pure function)."""
    commits: list[Commit] = []
    for raw in output.split(_RECORD_SEP):
        record = raw.strip("\n")
        if not record.strip():
            continue
        parts = record.split(_FIELD_SEP)
        if len(parts) != 4:
            raise CollectorError(
                f"Unexpected git log record with {len(parts)} fields (expected 4)."
            )
        sha, author, date, message = parts
        try:
            parsed_date = datetime.fromisoformat(date.strip())
        except ValueError as exc:
            raise CollectorError(f"Unparseable commit date: {date!r}") from exc
        commits.append(
            Commit(
                sha=sha.strip(),
                author=author.strip(),
                date=parsed_date,
                message=message.strip(),
            )
        )
    return commits


class CommitCollector:
    """Collects the most recent commits as typed Commit objects."""

    def __init__(self, run_git: GitRunner | None = None) -> None:
        self._run_git: GitRunner = run_git or _default_run_git

    def collect(self, config: CliConfig) -> list[Commit]:
        """Dispatch to local or remote collection based on the run mode."""
        if config.mode is Mode.REMOTE:
            assert config.url is not None  # guaranteed by Mode.REMOTE
            return self.collect_remote(config.url, config.count)
        return self.collect_local(Path(config.target), config.count)

    def collect_local(self, path: Path, count: int) -> list[Commit]:
        """Collect the most recent N (count) commits from a local repository."""
        if not path.exists():
            raise CollectorError(f"Path does not exist: {path}")
        self._ensure_git_repo(path)
        output = self._run_git(["log", "-n", str(count), _LOG_FORMAT], cwd=path)
        return _parse_log(output)

    def collect_remote(self, url: str, count: int) -> list[Commit]:
        """Shallow-clone the url to a temp dir and collect its recent commits."""
        with tempfile.TemporaryDirectory(prefix="commit-reviewer-") as tmp:
            clone_dir = Path(tmp) / "repo"
            self._run_git(
                ["clone", "--depth", str(count), "--no-tags", url, str(clone_dir)]
            )
            output = self._run_git(
                ["log", "-n", str(count), _LOG_FORMAT], cwd=clone_dir
            )
            return _parse_log(output)

    def _ensure_git_repo(self, path: Path) -> None:
        try:
            self._run_git(["rev-parse", "--is-inside-work-tree"], cwd=path)
        except CollectorError as exc:
            raise CollectorError(f"Not a git repository: {path}") from exc
