from __future__ import annotations

import time
from typing import Any

from openai import OpenAI

from clients.base import ChatBackend, ChatResult
from utils.chat import extract_choice_texts, serialize_response


class AittaDirectBackend(ChatBackend):
    backend_name = "aitta_direct"

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
        self.base_url = base_url
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> ChatResult:
        if kwargs.get("stream"):
            raise ValueError("Streaming is disabled for the Aitta demo path.")

        request_kwargs = {
            "model": kwargs.pop("model", self.model_name),
            "messages": messages,
        }
        for key in ("temperature", "top_p", "max_completion_tokens", "n", "response_format"):
            value = kwargs.pop(key, None)
            if value is not None:
                request_kwargs[key] = value
        request_kwargs.update(kwargs)

        started = time.perf_counter()
        response = self.client.chat.completions.create(**request_kwargs)
        latency_seconds = time.perf_counter() - started
        raw_response = serialize_response(response)
        return ChatResult(
            backend_name=self.backend_name,
            model_name=request_kwargs["model"],
            messages=messages,
            choices=extract_choice_texts(raw_response),
            latency_seconds=latency_seconds,
            raw_response=raw_response,
            usage=raw_response.get("usage"),
            resolved_base_url=self.base_url,
        )
