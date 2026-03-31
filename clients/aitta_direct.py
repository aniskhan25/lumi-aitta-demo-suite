from __future__ import annotations

import time

from typing import Any
from dataclasses import dataclass

from openai import OpenAI

from utils.chat import extract_choice_texts, serialize_response


@dataclass(slots=True)
class ChatResult:
    choices: list[str]
    latency_seconds: float
    usage: dict[str, Any] | None = None


class AittaDirectBackend:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model_name: str,
        timeout: float = 120.0,
    ) -> None:
        if not api_key:
            raise ValueError("AITTA API key is required for direct mode.")
        if not base_url:
            raise ValueError("A direct-mode base URL is required.")
        
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> ChatResult:
        request_kwargs = self._build_request_kwargs(messages, kwargs)

        started = time.perf_counter()
        response = self.client.chat.completions.create(**request_kwargs)
        latency_seconds = time.perf_counter() - started
        raw_response = serialize_response(response)

        return ChatResult(
            choices=extract_choice_texts(raw_response),
            latency_seconds=latency_seconds,
            usage=raw_response.get("usage"),
        )

    def _build_request_kwargs(
        self,
        messages: list[dict[str, Any]],
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        request_kwargs = {
            "model": kwargs.pop("model", self.model_name),
            "messages": messages,
        }

        for key in (
            "temperature",
            "top_p",
            "max_completion_tokens",
            "n",
        ):
            value = kwargs.pop(key, None)
            if value is not None:
                request_kwargs[key] = value
        
        request_kwargs.update(kwargs)
        return request_kwargs
