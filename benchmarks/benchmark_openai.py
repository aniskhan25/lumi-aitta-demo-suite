from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmarks.common import REPO_ROOT, add_backend_args
from clients.factory import build_backend
from utils.benchmarking import BenchmarkRecord, run_concurrent, summarize_records
from utils.config import load_runtime_config
from utils.files import write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Whole-response OpenAI-compatible benchmark runner.")
    add_backend_args(parser)
    parser.add_argument("--prompt-file", default=str(REPO_ROOT / "benchmarks" / "prompts" / "qa.txt"))
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-completion-tokens", type=int, default=256)
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--output", default=str(REPO_ROOT / "reports" / "example_outputs" / "benchmark_openai.json"))
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
    prompt = open(args.prompt_file, "r", encoding="utf-8").read().strip()

    def worker(index: int) -> BenchmarkRecord:
        started_at = time.time()
        messages = [
            {"role": "system", "content": "Answer accurately and concisely."},
            {"role": "user", "content": prompt},
        ]
        try:
            result = backend.complete(
                messages,
                temperature=args.temperature,
                top_p=args.top_p,
                max_completion_tokens=args.max_completion_tokens,
                n=args.n,
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

    records = run_concurrent(worker=worker, requests=args.requests, concurrency=args.concurrency)
    summary = summarize_records(records)
    payload = {
        "config": {
            "model_name": config.model_name,
            "backend_mode": "discovery" if config.use_discovery else "direct",
            "requests": args.requests,
            "concurrency": args.concurrency,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "max_completion_tokens": args.max_completion_tokens,
            "n": args.n,
            "prompt_file": args.prompt_file,
            "streaming_supported": False,
        },
        "summary": summary,
        "records": [asdict(record) for record in records],
    }
    write_json(args.output, payload)
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=True))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
