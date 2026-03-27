from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


def serialize_response(response: Any) -> dict[str, Any]:
    for method_name in ("model_dump", "to_dict", "dict"):
        method = getattr(response, method_name, None)
        if callable(method):
            payload = method()
            if isinstance(payload, dict):
                return payload
    if isinstance(response, dict):
        return response
    json_method = getattr(response, "json", None)
    if callable(json_method):
        return json.loads(json_method())
    raise TypeError("Unsupported response object type for serialization.")


def extract_choice_texts(payload: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for choice in payload.get("choices", []):
        message = choice.get("message", {})
        content = message.get("content", "")
        texts.append(content_to_text(content).strip())
    return texts


def content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                elif item.get("type") == "text" and "text" in item:
                    parts.append(str(item["text"]))
        return "\n".join(part for part in parts if part)
    if content is None:
        return ""
    return str(content)


def estimate_tokens_from_text(text: str) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


def estimate_tokens_from_messages(messages: list[dict[str, Any]]) -> int:
    total = 0
    for message in messages:
        total += 4
        total += estimate_tokens_from_text(message.get("role", ""))
        total += estimate_tokens_from_text(content_to_text(message.get("content", "")))
    return total + 2


def normalize_answer(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def majority_vote(candidates: list[str]) -> str:
    normalized = [normalize_answer(item) for item in candidates if item.strip()]
    if not normalized:
        return ""
    vote = Counter(normalized).most_common(1)[0][0]
    for original in candidates:
        if normalize_answer(original) == vote:
            return original
    return candidates[0]


def shortest_nonempty(candidates: list[str]) -> str:
    filtered = [candidate for candidate in candidates if candidate.strip()]
    return min(filtered, key=len) if filtered else ""


def read_text_lines(path: str | Path) -> list[str]:
    return [
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def maybe_parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
