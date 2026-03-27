from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from demos.common import REPO_ROOT, add_backend_args
from clients.factory import build_backend
from utils.chat import majority_vote, shortest_nonempty
from utils.config import load_runtime_config
from utils.files import read_documents


def choose_candidate(candidates: list[str], selector: str) -> str:
    if selector == "shortest":
        return shortest_nonempty(candidates)
    if selector == "majority":
        return majority_vote(candidates)
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-candidate reasoning demo using n completions.")
    add_backend_args(parser)
    parser.add_argument("--prompt-dir", default=str(REPO_ROOT / "data" / "benchmark_inputs" / "reasoning"))
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--selector", choices=("none", "shortest", "majority"), default="majority")
    args = parser.parse_args()

    config = load_runtime_config(
        model_name=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        use_discovery=args.discovery,
        api_root=args.api_root,
    )
    backend = build_backend(config)
    results: list[dict[str, object]] = []
    for path, text in read_documents(args.prompt_dir):
        messages = [
            {
                "role": "system",
                "content": "Provide a concise, high-quality answer. Keep reasoning implicit.",
            },
            {"role": "user", "content": text},
        ]
        result = backend.complete(
            messages,
            temperature=args.temperature,
            top_p=args.top_p,
            max_completion_tokens=args.max_completion_tokens,
            n=args.n,
        )
        selected = choose_candidate(result.choices, args.selector)
        results.append(
            {
                "prompt_file": path.name,
                "candidates": result.choices,
                "selected": selected or None,
                "latency_seconds": round(result.latency_seconds, 3),
            }
        )

    print(json.dumps(results, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
