from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from demos.common import add_backend_args
from clients.factory import build_backend
from utils.config import load_runtime_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Aitta smoke test for direct or discovery mode.")
    add_backend_args(parser)
    parser.add_argument("--prompt", default="Summarize Aitta usage in one sentence.")
    args = parser.parse_args()

    config = load_runtime_config(
        model_key=args.model_key,
        mode=args.mode,
        api_key=args.api_key,
        base_url=args.base_url,
        model_name=args.model_name,
        env_file=args.env_file,
    )
    backend = build_backend(config)
    messages = [
        {"role": "system", "content": "You are a concise smoke-test assistant."},
        {"role": "user", "content": args.prompt},
    ]
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
    if result.metadata:
        description = result.metadata.get("description")
        if description:
            print(f"description={description}")
    print("\n--- response ---")
    print(result.primary_text)


if __name__ == "__main__":
    main()
