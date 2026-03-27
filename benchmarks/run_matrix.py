from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmarks.common import REPO_ROOT, add_backend_args
from clients.factory import build_backend
from utils.benchmarking import BenchmarkRecord, run_concurrent, summarize_records
from utils.config import load_runtime_config
from utils.files import write_json


def execute_run(
    *,
    backend,
    prompt: str,
    requests: int,
    concurrency: int,
    temperature: float,
    top_p: float,
    max_completion_tokens: int,
    n: int,
) -> dict[str, object]:
    def worker(index: int) -> BenchmarkRecord:
        started_at = time.time()
        messages = [
            {"role": "system", "content": "Answer accurately and concisely."},
            {"role": "user", "content": prompt},
        ]
        try:
            result = backend.complete(
                messages,
                temperature=temperature,
                top_p=top_p,
                max_completion_tokens=max_completion_tokens,
                n=n,
            )
            return BenchmarkRecord(
                index=index,
                success=True,
                latency_seconds=result.latency_seconds,
                error=None,
                usage=result.usage,
                response_texts=result.choices,
                started_at=started_at,
            )
        except Exception as exc:
            return BenchmarkRecord(
                index=index,
                success=False,
                latency_seconds=time.time() - started_at,
                error=str(exc),
                usage=None,
                response_texts=[],
                started_at=started_at,
            )

    records = run_concurrent(worker=worker, requests=requests, concurrency=concurrency)
    return {
        "summary": summarize_records(records),
        "records": [asdict(record) for record in records],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a benchmark matrix for latency, concurrency, and throughput.")
    add_backend_args(parser)
    parser.add_argument("--prompt-file", default=str(REPO_ROOT / "benchmarks" / "prompts" / "qa.txt"))
    parser.add_argument("--requests", type=int, default=20, help="Requests per benchmark point.")
    parser.add_argument("--baseline-concurrency", type=int, default=1)
    parser.add_argument("--concurrency-values", nargs="+", type=int, default=[1, 2, 4, 8])
    parser.add_argument("--max-token-values", nargs="+", type=int, default=[64, 128, 256])
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "reports" / "example_outputs" / "benchmark_matrix.json"),
    )
    args = parser.parse_args()

    config = load_runtime_config(
        model_name=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
    )
    backend = build_backend(config)
    prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()

    baseline = execute_run(
        backend=backend,
        prompt=prompt,
        requests=args.requests,
        concurrency=args.baseline_concurrency,
        temperature=args.temperature,
        top_p=args.top_p,
        max_completion_tokens=max(args.max_token_values),
        n=args.n,
    )

    concurrency_sweep: list[dict[str, object]] = []
    for concurrency in args.concurrency_values:
        run = execute_run(
            backend=backend,
            prompt=prompt,
            requests=args.requests,
            concurrency=concurrency,
            temperature=args.temperature,
            top_p=args.top_p,
            max_completion_tokens=max(args.max_token_values),
            n=args.n,
        )
        concurrency_sweep.append(
            {
                "concurrency": concurrency,
                "summary": run["summary"],
            }
        )

    token_sweep: list[dict[str, object]] = []
    for max_tokens in args.max_token_values:
        run = execute_run(
            backend=backend,
            prompt=prompt,
            requests=args.requests,
            concurrency=args.baseline_concurrency,
            temperature=args.temperature,
            top_p=args.top_p,
            max_completion_tokens=max_tokens,
            n=args.n,
        )
        token_sweep.append(
            {
                "max_completion_tokens": max_tokens,
                "summary": run["summary"],
            }
        )

    payload = {
        "config": {
            "model_name": config.model_name,
            "backend_mode": "direct",
            "prompt_file": args.prompt_file,
            "requests": args.requests,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "n": args.n,
        },
        "baseline": {
            "concurrency": args.baseline_concurrency,
            "max_completion_tokens": max(args.max_token_values),
            "summary": baseline["summary"],
        },
        "concurrency_sweep": concurrency_sweep,
        "token_sweep": token_sweep,
    }
    write_json(args.output, payload)
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
