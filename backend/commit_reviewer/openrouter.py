"""HTTP client for the OpenRouter chat-completions API."""

from __future__ import annotations

import os
from typing import Any, Protocol

import httpx

from . import OPENROUTER_MODEL
from .errors import EvaluatorError

_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
_API_KEY_ENV = "OPENROUTER_API_KEY"


class ChatClient(Protocol):
    """Minimal chat interface the evaluator depends on (keeps it HTTP-free)."""

    def complete(
        self,
        system: str,
        user: str,
        response_format: dict[str, Any] | None = None,
    ) -> str: ...


class OpenRouterClient:
    """Thin wrapper over the OpenRouter chat-completions endpoint."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = OPENROUTER_MODEL,
        base_url: str = _BASE_URL,
        timeout: float = 45.0,
        temperature: float = 0.2,
        max_tokens: int = 512,
        reasoning_effort: str | None = "low",
        client: httpx.Client | None = None,
    ) -> None:
        key = api_key or os.environ.get(_API_KEY_ENV)
        if not key:
            raise EvaluatorError(
                f"{_API_KEY_ENV} is not set. Add it to your environment or a .env file "
                "(see .env.example)."
            )
        self._api_key = key
        self._model = model
        self._base_url = base_url
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._reasoning_effort = reasoning_effort
        self._client = client or httpx.Client(timeout=timeout)

    def complete(
        self,
        system: str,
        user: str,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Send a system+user prompt and return the assistant message content."""
        payload: dict[str, Any] = {
            "model": self._model,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if response_format is not None:
            payload["response_format"] = response_format
        if self._reasoning_effort is not None:
            # Keep the model's chain-of-thought short: less reasoning means
            # faster responses and fewer corrupted Harmony message headers.
            payload["reasoning"] = {"effort": self._reasoning_effort}

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "X-Title": "commit-reviewer",
        }

        try:
            response = self._client.post(self._base_url, headers=headers, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text.strip()
            raise EvaluatorError(
                f"OpenRouter returned HTTP {exc.response.status_code}: {body}"
            ) from exc
        except httpx.HTTPError as exc:
            raise EvaluatorError(f"OpenRouter request failed: {exc}") from exc

        data = response.json()

        # OpenRouter often returns HTTP 200 with an embedded error object
        # (e.g. an upstream 502) instead of a completion; surface it cleanly.
        if isinstance(data, dict) and data.get("error"):
            error = data["error"]
            if isinstance(error, dict):
                code = error.get("code")
                message = error.get("message")
                raise EvaluatorError(f"OpenRouter error {code}: {message}")
            raise EvaluatorError(f"OpenRouter error: {error!r}")

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise EvaluatorError(
                f"Unexpected OpenRouter response shape: {data!r}"
            ) from exc
        if not isinstance(content, str):
            raise EvaluatorError(f"OpenRouter content was not text: {content!r}")
        return content

    def close(self) -> None:
        self._client.close()
