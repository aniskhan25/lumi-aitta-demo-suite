from __future__ import annotations

import json
import re
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
def normalize_answer(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()
