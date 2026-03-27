from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from demos.common import REPO_ROOT, add_backend_args
from clients.factory import build_backend
from utils.chat import estimate_tokens_from_messages, read_text_lines
from utils.config import load_runtime_config


def summarize_history(backend, summary: str, archived_turns: list[dict[str, str]], args) -> str:
    transcript = "\n".join(
        f"{message['role'].upper()}: {message['content']}" for message in archived_turns
    )
    messages = [
        {
            "role": "system",
            "content": "Summarize older conversation state for future assistant turns.",
        },
        {
            "role": "user",
            "content": (
                f"Existing summary:\n{summary or '(none)'}\n\n"
                f"New archived turns:\n{transcript}\n\n"
                "Return a compact memory summary with facts, preferences, and open tasks."
            ),
        },
    ]
    result = backend.complete(
        messages,
        temperature=min(args.temperature, 0.3),
        top_p=args.top_p,
        max_completion_tokens=min(args.max_completion_tokens, 200),
        n=1,
    )
    return result.primary_text.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Client-managed multi-turn memory demo.")
    add_backend_args(parser)
    parser.add_argument("--turn-file", default=str(REPO_ROOT / "data" / "benchmark_inputs" / "multiturn_prompts.txt"))
    parser.add_argument("--recent-turns", type=int, default=4)
    args = parser.parse_args()

    config = load_runtime_config(
        model_name=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        use_discovery=args.discovery,
        api_root=args.api_root,
    )
    backend = build_backend(config)
    planned_turns = read_text_lines(args.turn_file)
    recent_history: deque[dict[str, str]] = deque(maxlen=args.recent_turns * 2)
    archived_buffer: list[dict[str, str]] = []
    summary = ""
    transcript_rows: list[dict[str, object]] = []

    for turn_index, user_prompt in enumerate(planned_turns, start=1):
        if len(recent_history) == recent_history.maxlen:
            archived_buffer.extend(list(recent_history)[:2])
            while len(recent_history) > recent_history.maxlen - 2:
                recent_history.popleft()
            summary = summarize_history(backend, summary, archived_buffer, args)
            archived_buffer.clear()

        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": "You are a helpful assistant in a client-managed memory demo.",
            }
        ]
        if summary:
            messages.append({"role": "system", "content": f"Older conversation summary:\n{summary}"})
        messages.extend(list(recent_history))
        messages.append({"role": "user", "content": user_prompt})

        result = backend.complete(
            messages,
            temperature=args.temperature,
            top_p=args.top_p,
            max_completion_tokens=args.max_completion_tokens,
            n=1,
        )
        assistant_text = result.primary_text.strip()
        recent_history.append({"role": "user", "content": user_prompt})
        recent_history.append({"role": "assistant", "content": assistant_text})

        prompt_tokens = estimate_tokens_from_messages(messages)
        transcript_rows.append(
            {
                "turn": turn_index,
                "user": user_prompt,
                "assistant": assistant_text,
                "prompt_tokens_estimate": prompt_tokens,
                "verbatim_turns_retained": len(recent_history) // 2,
                "has_summary": bool(summary),
            }
        )

    print(json.dumps(transcript_rows, indent=2, ensure_ascii=True))
    if summary:
        print("\n--- archived_summary ---")
        print(summary)


if __name__ == "__main__":
    main()
