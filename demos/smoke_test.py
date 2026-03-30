from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from clients import build_backend
from utils.config import load_runtime_config
from utils.cli import add_backend_args


def main() -> None:
    parser = argparse.ArgumentParser(description="Aitta smoke test for the OpenAI-compatible endpoint.")
    add_backend_args(parser)
    parser.add_argument("--prompt", default="Summarize Aitta usage in one sentence.")
    parser.add_argument("--stream", action="store_true", help="Stream the direct endpoint response token-by-token.")
    args = parser.parse_args()

    config = load_runtime_config(
        model_name=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
    )
    backend = build_backend(config)
    messages = [
        {"role": "system", "content": "You are a concise smoke-test assistant."},
        {"role": "user", "content": args.prompt},
    ]
    if args.stream:
        print(f"backend={backend.backend_name}")
        print(f"model={config.model_name}")
        print(f"resolved_base_url={config.base_url}")
        print("\n--- response ---")
        for token in backend.stream_text(
            messages,
            temperature=args.temperature,
            top_p=args.top_p,
            max_completion_tokens=args.max_completion_tokens,
        ):
            print(token, end="", flush=True)
        print()
        return

    result = backend.complete(
        messages,
        temperature=args.temperature,
        top_p=args.top_p,
        max_completion_tokens=args.max_completion_tokens,
        n=1,
    )

    print(f"backend={result.backend_name}")
    print(f"model={result.model_name}")
    print(f"latency_seconds={result.latency_seconds:.3f}")
    print(f"resolved_base_url={result.resolved_base_url or ''}")
    if result.usage:
        print("usage=" + json.dumps(result.usage, ensure_ascii=True))
    print("\n--- response ---")
    print(result.primary_text)


if __name__ == "__main__":
    main()
