from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from clients.base import ChatBackend, ChatResult
from utils.chat import extract_choice_texts


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
        self.api_key = api_key
        self.timeout = timeout

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
        raw_response = self._post_chat_completions(request_kwargs)
        latency_seconds = time.perf_counter() - started
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

    def _post_chat_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        endpoint = self._chat_completions_url(self.base_url)
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Aitta request failed with HTTP {exc.code}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach Aitta endpoint: {exc.reason}") from exc

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Aitta returned a non-JSON response.") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("Aitta returned an unexpected response payload.")
        return payload

    @staticmethod
    def _chat_completions_url(base_url: str) -> str:
        normalized = base_url.rstrip("/")
        if normalized.endswith("/chat/completions"):
            return normalized
        if normalized.endswith("/v1"):
            return normalized + "/chat/completions"
        parsed = urllib.parse.urlparse(normalized)
        path = parsed.path.rstrip("/")
        if path.endswith("/v1"):
            new_path = path + "/chat/completions"
        else:
            new_path = path + "/v1/chat/completions"
        return urllib.parse.urlunparse(parsed._replace(path=new_path))
