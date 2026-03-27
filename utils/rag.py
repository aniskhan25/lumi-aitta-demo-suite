from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

from utils.chat import estimate_tokens_from_messages, estimate_tokens_from_text
from utils.files import read_documents


@dataclass
class Chunk:
    source: str
    chunk_id: str
    text: str
    score: float = 0.0


def chunk_documents(path: str | Path, *, chunk_words: int = 180, overlap_words: int = 30) -> list[Chunk]:
    chunks: list[Chunk] = []
    for file_path, text in read_documents(path):
        words = text.split()
        if not words:
            continue
        start = 0
        index = 0
        while start < len(words):
            end = min(len(words), start + chunk_words)
            chunk_text = " ".join(words[start:end]).strip()
            if chunk_text:
                chunks.append(
                    Chunk(
                        source=file_path.name,
                        chunk_id=f"{file_path.stem}-{index}",
                        text=chunk_text,
                    )
                )
            if end == len(words):
                break
            start = max(0, end - overlap_words)
            index += 1
    return chunks


def retrieve_chunks(chunks: list[Chunk], query: str, *, top_k: int = 3) -> list[Chunk]:
    query_terms = tokenize(query)
    if not query_terms:
        return chunks[:top_k]
    scored: list[Chunk] = []
    for chunk in chunks:
        chunk_terms = tokenize(chunk.text)
        overlap = sum(1 for term in query_terms if term in chunk_terms)
        if overlap == 0:
            continue
        chunk.score = overlap / math.sqrt(len(chunk_terms) or 1)
        scored.append(chunk)
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_k]


def build_rag_messages(question: str, retrieved_chunks: list[Chunk]) -> list[dict[str, str]]:
    context_blocks = []
    for chunk in retrieved_chunks:
        context_blocks.append(f"[{chunk.source}::{chunk.chunk_id}]\n{chunk.text}")
    context_text = "\n\n".join(context_blocks)
    return [
        {
            "role": "system",
            "content": (
                "Answer only from the provided context. "
                "If the answer is not present, say that the context does not contain it."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Context:\n{context_text}\n\n"
                f"Question: {question}\n\n"
                "Return a concise answer and cite the chunk ids you used."
            ),
        },
    ]


def budget_report(messages: list[dict[str, str]], max_completion_tokens: int, *, sequence_limit: int = 8192) -> dict[str, int | float]:
    system_tokens = estimate_tokens_from_text(messages[0]["content"]) if messages else 0
    user_tokens = estimate_tokens_from_text(messages[-1]["content"]) if messages else 0
    prompt_tokens = estimate_tokens_from_messages(messages)
    total_request_tokens = prompt_tokens + max_completion_tokens
    usage_ratio = total_request_tokens / sequence_limit if sequence_limit else 0.0
    return {
        "system_tokens": system_tokens,
        "user_and_context_tokens": user_tokens,
        "prompt_tokens": prompt_tokens,
        "requested_completion_tokens": max_completion_tokens,
        "estimated_total_tokens": total_request_tokens,
        "sequence_limit": sequence_limit,
        "usage_ratio": round(usage_ratio, 3),
    }


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 1}
