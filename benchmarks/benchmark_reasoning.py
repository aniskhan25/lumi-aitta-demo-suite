from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmarks.common import REPO_ROOT, add_backend_args
from clients.factory import build_backend
from utils.chat import normalize_answer
from utils.config import load_runtime_config
from utils.files import list_text_files, write_json


def diversity_score(candidates: list[str]) -> float:
    normalized = [normalize_answer(candidate) for candidate in candidates if candidate.strip()]
    if not normalized:
        return 0.0
    return round(len(set(normalized)) / len(normalized), 3)


def agreement_score(candidates: list[str]) -> float:
    normalized = [normalize_answer(candidate) for candidate in candidates if candidate.strip()]
    if not normalized:
        return 0.0
    most_common = max(normalized.count(item) for item in set(normalized))
    return round(most_common / len(normalized), 3)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reasoning benchmark across n completions.")
    add_backend_args(parser)
    parser.add_argument("--prompt-dir", default=str(REPO_ROOT / "data" / "benchmark_inputs" / "reasoning"))
    parser.add_argument("--n-values", nargs="+", type=int, default=[1, 3, 5])
    parser.add_argument("--temperature", type=float, default=0.4)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-completion-tokens", type=int, default=256)
    parser.add_argument("--output", default=str(REPO_ROOT / "reports" / "example_outputs" / "benchmark_reasoning.json"))
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
    prompt_files = list_text_files(args.prompt_dir)
    results: list[dict[str, object]] = []

    for n_value in args.n_values:
        run_started = time.perf_counter()
        total_tokens = 0
        failures = 0
        rows: list[dict[str, object]] = []
        latencies: list[float] = []
        for path in prompt_files:
            prompt = path.read_text(encoding="utf-8").strip()
            messages = [
                {"role": "system", "content": "Return a concise answer. Keep reasoning implicit."},
                {"role": "user", "content": prompt},
            ]
            try:
                result = backend.complete(
                    messages,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    max_completion_tokens=args.max_completion_tokens,
                    n=n_value,
                )
                latencies.append(result.latency_seconds)
                if result.usage:
                    total_tokens += int(result.usage.get("completion_tokens", 0))
                rows.append(
                    {
                        "prompt_file": path.name,
                        "latency_seconds": round(result.latency_seconds, 3),
                        "candidate_diversity": diversity_score(result.choices),
                        "normalized_answer_agreement": agreement_score(result.choices),
                        "candidates": result.choices,
                    }
                )
            except Exception as exc:
                failures += 1
                rows.append({"prompt_file": path.name, "error": str(exc)})
        wall_time = time.perf_counter() - run_started
        results.append(
            {
                "n": n_value,
                "wall_time_seconds": round(wall_time, 3),
                "avg_latency_seconds": round(sum(latencies) / len(latencies), 3) if latencies else 0.0,
                "total_tokens_returned": total_tokens,
                "failure_rate": round(failures / len(prompt_files), 3) if prompt_files else 0.0,
                "candidate_diversity_avg": round(
                    sum(row["candidate_diversity"] for row in rows if "candidate_diversity" in row) / max(1, len(latencies)),
                    3,
                ),
                "normalized_agreement_avg": round(
                    sum(row["normalized_answer_agreement"] for row in rows if "normalized_answer_agreement" in row) / max(1, len(latencies)),
                    3,
                ),
                "rows": rows,
            }
        )

    payload = {
        "config": {
            "model_name": config.model_name,
            "backend_mode": "discovery" if config.use_discovery else "direct",
            "temperature": args.temperature,
            "top_p": args.top_p,
            "max_completion_tokens": args.max_completion_tokens,
        },
        "results": results,
    }
    write_json(args.output, payload)
    print(json.dumps(results, indent=2, ensure_ascii=True))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
