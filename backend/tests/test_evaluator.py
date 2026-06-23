"""Tests for the LLM commit evaluator.

    A FakeClient stands in for the chat client, recording calls and
    replaying queued responses (strings or exceptions), so no network
    or real model is used. Each category below is delimited in the code
    with banner comments  "CATEGORY: <name>" ... "end: <name>".

    Happy path
        a valid structured-JSON response is validated into an
        Evaluation with the right rating and reasoning.

    Contract
        the strict RESPONSE_FORMAT schema is forwarded on every call.

    Validation fallback
        a response with an invalid rating fails validation and yields
        the safe fallback (bad) instead of raising.

    Resilience
        a persistent client error triggers retries (with sleep patched
        out) and then the fallback, asserting the exact attempt count.

    Aggregation
        exactly one evaluation is produced per commit, in input order.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from commit_reviewer.errors import EvaluatorError
from commit_reviewer.evaluator import RESPONSE_FORMAT, LLMCommitEvaluator
from commit_reviewer.models import Commit, Rating


class FakeClient:
    """Records calls and replays queued responses (strings or exceptions)."""

    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        system: str,
        user: str,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        self.calls.append(
            {"system": system, "user": user, "response_format": response_format}
        )
        result = self.responses[min(len(self.calls) - 1, len(self.responses) - 1)]
        if isinstance(result, Exception):
            raise result
        return str(result)


def _commit(message: str = "feat: x", sha: str = "abc1234") -> Commit:
    return Commit(sha=sha, author="Jane", date=datetime(2024, 1, 1), message=message)


# ======================================================================
# CATEGORY: Happy path
# ======================================================================


def test_valid_response_parsed() -> None:
    client = FakeClient(['{"rating":"excellent","reasoning":"Clear."}'])
    [evaluation] = LLMCommitEvaluator(client).evaluate([_commit()])
    assert evaluation.rating is Rating.EXCELLENT
    assert evaluation.reasoning == "Clear."


# end: Happy path


# ======================================================================
# CATEGORY: Contract
# ======================================================================


def test_response_format_is_forwarded() -> None:
    client = FakeClient(['{"rating":"good","reasoning":"ok"}'])
    LLMCommitEvaluator(client).evaluate([_commit()])
    assert client.calls[0]["response_format"] == RESPONSE_FORMAT


# end: Contract


# ======================================================================
# CATEGORY: Validation fallback
# ======================================================================


def test_invalid_rating_falls_back_to_bad() -> None:
    client = FakeClient(['{"rating":"meh","reasoning":"x"}'])
    [evaluation] = LLMCommitEvaluator(client, max_retries=0).evaluate([_commit()])
    assert evaluation.rating is Rating.BAD


# end: Validation fallback


# ======================================================================
# CATEGORY: Resilience
# ======================================================================


def test_persistent_error_retries_then_falls_back() -> None:
    client = FakeClient([EvaluatorError("boom")])
    evaluator = LLMCommitEvaluator(client, max_retries=2, sleep=lambda _: None)
    [evaluation] = evaluator.evaluate([_commit()])
    assert evaluation.rating is Rating.BAD
    assert "LLM error" in evaluation.reasoning
    assert len(client.calls) == 3  # initial + 2 retries


# end: Resilience


# ======================================================================
# CATEGORY: Aggregation
# ======================================================================


def test_one_evaluation_per_commit_in_order() -> None:
    client = FakeClient(
        [
            '{"rating":"excellent","reasoning":"a"}',
            '{"rating":"bad","reasoning":"b"}',
        ]
    )
    commits = [_commit(sha="c1"), _commit(sha="c2")]
    evaluations = LLMCommitEvaluator(client).evaluate(commits)
    assert [e.rating for e in evaluations] == [Rating.EXCELLENT, Rating.BAD]


# end: Aggregation
