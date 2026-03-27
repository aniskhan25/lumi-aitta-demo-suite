from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

ChatMessage = dict[str, Any]


@dataclass(slots=True)
class ChatResult:
    backend_name: str
    model_name: str
    messages: list[ChatMessage]
    choices: list[str]
    latency_seconds: float
    raw_response: dict[str, Any]
    usage: dict[str, Any] | None = None
    resolved_base_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def primary_text(self) -> str:
        return self.choices[0] if self.choices else ""


class ChatBackend:
    backend_name = "base"

    def complete(self, messages: list[ChatMessage], **kwargs: Any) -> ChatResult:
        raise NotImplementedError

    def stream_text(self, messages: list[ChatMessage], **kwargs: Any) -> Iterable[str]:
        raise NotImplementedError
