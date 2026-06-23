"""Evaluate commit messages with an LLM and validate the structured result."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from .errors import EvaluatorError
from .models import Commit, Evaluation, Rating
from .openrouter import ChatClient

logger = logging.getLogger("commit_reviewer")

#: Called once per commit as soon as its evaluation is ready (for live output).
ResultCallback = Callable[[int, int, Commit, Evaluation], None]

#: Ask for a plain JSON object. The free provider does not reliably honor the
#: stricter json_schema grammar for this reasoning model (it still emits invalid
#: JSON), so json_object plus prompt + pydantic validation is more robust.
RESPONSE_FORMAT: dict[str, Any] = {"type": "json_object"}

SYSTEM_PROMPT = """\
You are a senior engineer reviewing git commit messages. Rate the quality of a \
single commit message using exactly one of these ratings:

- "excellent": Clear, concise subject in the imperative mood; explains WHAT changed \
and WHY when useful; well-structured; follows good conventions.
- "good": Understandable and reasonable, but with minor issues (vague wording, \
missing context, or style nits).
- "bad": Unclear, uninformative, or unhelpful (e.g. "fix", "wip", "update stuff", \
empty, or noise).

Judge only the commit MESSAGE quality, not the code. Respond with a brief, specific \
reasoning (1-2 sentences). You must respond with JSON only, matching the required \
schema: {"rating": <excellent|good|bad>, "reasoning": <string>}."""


class LLMCommitEvaluator:
    """Calls the LLM per commit and returns validated evaluations."""

    def __init__(
        self,
        client: ChatClient,
        *,
        max_retries: int = 2,
        backoff_base: float = 0.5,
        sleep: Any = time.sleep,
        on_result: ResultCallback | None = None,
    ) -> None:
        self._client = client
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._sleep = sleep
        self._on_result = on_result

    def evaluate(self, commits: list[Commit]) -> list[Evaluation]:
        """Evaluate each commit, logging to file and streaming results out."""
        evaluations: list[Evaluation] = []
        total = len(commits)
        for index, commit in enumerate(commits, start=1):
            started = time.perf_counter()
            evaluation = self._evaluate_one(commit)
            elapsed = time.perf_counter() - started
            evaluations.append(evaluation)
            logger.info(
                "[%d/%d] %s  %-9s  (%.2fs)  %s",
                index,
                total,
                commit.short_sha,
                evaluation.rating.value.upper(),
                elapsed,
                evaluation.reasoning,
            )
            if self._on_result is not None:
                self._on_result(index, total, commit, evaluation)
        return evaluations

    def _evaluate_one(self, commit: Commit) -> Evaluation:
        user_prompt = self._build_user_prompt(commit)
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                content = self._client.complete(
                    SYSTEM_PROMPT, user_prompt, response_format=RESPONSE_FORMAT
                )
                return self._parse(content)
            except (EvaluatorError, ValidationError, ValueError) as exc:
                last_error = exc
                if attempt < self._max_retries:
                    delay = self._backoff_base * (2**attempt)
                    logger.warning(
                        "Evaluation attempt %d for %s failed (%s); retrying in %.1fs",
                        attempt + 1,
                        commit.short_sha,
                        exc,
                        delay,
                    )
                    self._sleep(delay)

        logger.error(
            "Giving up on %s after %d attempts: %s",
            commit.short_sha,
            self._max_retries + 1,
            last_error,
        )
        return Evaluation(
            rating=Rating.BAD,
            reasoning=f"Could not evaluate this commit (LLM error: {last_error}).",
        )

    @staticmethod
    def _parse(content: str) -> Evaluation:
        """Validate the model output, tolerating raw control characters.

        The free model frequently returns otherwise-valid JSON with literal
        tabs/newlines inside string values. pydantic's strict JSON reader
        rejects those, so we parse with the standard library in non-strict
        mode (which allows control characters) and then validate the object.
        """
        data = json.loads(content, strict=False)
        return Evaluation.model_validate(data)

    @staticmethod
    def _build_user_prompt(commit: Commit) -> str:
        return f"Evaluate this commit message:\n\n{commit.message}"
