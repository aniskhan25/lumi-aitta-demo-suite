from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

from clients.aitta_direct import AittaDirectBackend
from utils.benchmarking import make_chat_worker, run_concurrent, summarize_records
from utils.cli import add_backend_args
from utils.config import load_runtime_config
from utils.files import write_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Whole-response OpenAI-compatible benchmark runner."
    )
    add_backend_args(parser)
    parser.add_argument(
        "--prompt-file", default=str(REPO_ROOT / "benchmarks" / "prompts" / "qa.txt")
    )
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-completion-tokens", type=int, default=256)
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument(
        "--output",
        default=str(
            REPO_ROOT / "reports" / "example_outputs" / "benchmark_openai.json"
        ),
    )
    args = parser.parse_args()

    config = load_runtime_config(
        model_name=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
    )
    backend = AittaDirectBackend(
        api_key=config.api_key,
        base_url=config.base_url,
        model_name=config.model_name,
        timeout=config.timeout_seconds,
    )
    prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    worker = make_chat_worker(
        backend=backend,
        prompt=prompt,
        temperature=args.temperature,
        top_p=args.top_p,
        max_completion_tokens=args.max_completion_tokens,
        n=args.n,
    )
    records = run_concurrent(worker=worker, requests=args.requests, concurrency=args.concurrency)
    summary = summarize_records(records)
    payload = {
        "config": {
            "model_name": config.model_name,
            "backend_mode": "direct",
            "requests": args.requests,
            "concurrency": args.concurrency,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "max_completion_tokens": args.max_completion_tokens,
            "n": args.n,
            "prompt_file": args.prompt_file,
        },
        "summary": summary,
        "records": [asdict(record) for record in records],
    }
    write_json(args.output, payload)
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=True))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
