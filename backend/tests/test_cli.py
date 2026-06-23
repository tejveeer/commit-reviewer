"""Tests for CLI parsing, env loading, and orchestration.

    Fake collector/evaluator doubles and monkeypatch keep these tests
    offline and filesystem-isolated (the web root is redirected to
    tmp_path). Each category below is delimited in the code with banner
    comments  "CATEGORY: <name>" ... "end: <name>".

    Argument parsing
        defaults, remote --url, --no-serve, and rejection of a
        non-positive --count.

    Repo labeling
        _repo_label resolves a local path and passes through a remote
        URL unchanged.

    Env loading (regression)
        _load_env finds the project .env from an unrelated working
        directory, and never overrides an already-set env var.

    Orchestration
        run writes a schema-correct report end-to-end with injected
        doubles, and skips the evaluator when there are no commits.

    Error handling
        main maps a CommitReviewerError to exit code 1.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from commit_reviewer import DEFAULT_COMMIT_COUNT, DEFAULT_PORT, OPENROUTER_MODEL, cli
from commit_reviewer.config import CliConfig
from commit_reviewer.errors import CommitReviewerError
from commit_reviewer.models import Commit, Evaluation, Mode, Report


class FakeCollector:
    def __init__(self, commits: list[Commit]) -> None:
        self._commits = commits

    def collect(self, config: CliConfig) -> list[Commit]:
        return self._commits


class FakeEvaluator:
    def __init__(self, evaluations: list[Evaluation]) -> None:
        self._evaluations = evaluations
        self.called = False

    def evaluate(self, commits: list[Commit]) -> list[Evaluation]:
        self.called = True
        return self._evaluations


# ======================================================================
# CATEGORY: Argument parsing
# ======================================================================


def test_parse_args_defaults() -> None:
    config = cli.parse_args([])
    assert config.mode is Mode.LOCAL
    assert config.target == "."
    assert config.count == DEFAULT_COMMIT_COUNT
    assert config.port == DEFAULT_PORT
    assert config.model == OPENROUTER_MODEL
    assert config.serve is True


def test_parse_args_remote() -> None:
    config = cli.parse_args(["--url", "https://example.com/x.git"])
    assert config.mode is Mode.REMOTE
    assert config.url == "https://example.com/x.git"


def test_parse_args_no_serve() -> None:
    assert cli.parse_args(["--no-serve"]).serve is False


def test_parse_args_invalid_count_exits() -> None:
    with pytest.raises(SystemExit):
        cli.parse_args(["-n", "0"])


# end: Argument parsing


# ======================================================================
# CATEGORY: Repo labeling
# ======================================================================


def test_repo_label_local() -> None:
    config = cli.parse_args([])
    assert cli._repo_label(config) == str(Path(".").resolve())


def test_repo_label_remote() -> None:
    config = cli.parse_args(["--url", "https://example.com/x.git"])
    assert cli._repo_label(config) == "https://example.com/x.git"


# end: Repo labeling


# ======================================================================
# CATEGORY: Env loading (regression)
# ======================================================================


def test_load_env_from_unrelated_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".env").write_text("OPENROUTER_API_KEY=from-dotenv\n")

    workdir = tmp_path / "elsewhere"
    workdir.mkdir()
    monkeypatch.chdir(workdir)

    cli._load_env(project_root=project_root)
    import os

    assert os.environ["OPENROUTER_API_KEY"] == "from-dotenv"


def test_load_env_does_not_override_existing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "preexisting")
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".env").write_text("OPENROUTER_API_KEY=from-dotenv\n")

    cli._load_env(project_root=project_root)
    import os

    assert os.environ["OPENROUTER_API_KEY"] == "preexisting"


# end: Env loading (regression)


# ======================================================================
# CATEGORY: Orchestration
# ======================================================================


def test_run_writes_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sample_commits: list[Commit],
    sample_evaluations: list[Evaluation],
) -> None:
    monkeypatch.setattr(cli, "default_web_root", lambda: tmp_path)
    config = CliConfig(
        mode=Mode.LOCAL, target=".", count=5, port=3546, model="m", serve=False
    )
    evaluator = FakeEvaluator(sample_evaluations)

    rc = cli.run(config, collector=FakeCollector(sample_commits), evaluator=evaluator)  # type: ignore[arg-type]

    assert rc == 0
    assert evaluator.called
    report = Report.model_validate_json((tmp_path / "report.json").read_text())
    assert len(report.commits) == 2
    assert report.summary.excellent == 1
    assert report.summary.bad == 1


def test_run_empty_commits_skips_evaluator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "default_web_root", lambda: tmp_path)
    config = CliConfig(
        mode=Mode.LOCAL, target=".", count=5, port=3546, model="m", serve=False
    )
    evaluator = FakeEvaluator([])

    rc = cli.run(config, collector=FakeCollector([]), evaluator=evaluator)  # type: ignore[arg-type]

    assert rc == 0
    assert evaluator.called is False
    report = Report.model_validate_json((tmp_path / "report.json").read_text())
    assert report.commits == []


# end: Orchestration


# ======================================================================
# CATEGORY: Error handling
# ======================================================================


def test_main_handles_known_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(config: CliConfig) -> int:
        raise CommitReviewerError("nope")

    monkeypatch.setattr(cli, "run", boom)
    assert cli.main([]) == 1


# end: Error handling
