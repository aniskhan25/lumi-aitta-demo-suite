from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from demos.common import REPO_ROOT, add_backend_args
from clients.factory import build_backend
from utils.config import load_runtime_config
from utils.files import read_documents, write_csv, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch summarization demo.")
    add_backend_args(parser)
    parser.add_argument("--input-dir", default=str(REPO_ROOT / "data" / "benchmark_inputs" / "summaries"))
    parser.add_argument("--output", default=str(REPO_ROOT / "reports" / "example_outputs" / "batch_summaries.jsonl"))
    parser.add_argument("--format", choices=("jsonl", "csv"), default="jsonl")
    args = parser.parse_args()

    config = load_runtime_config(
        model_name=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
    )
    backend = build_backend(config)
    rows: list[dict[str, object]] = []
    started = time.perf_counter()
    for path, text in read_documents(args.input_dir):
        messages = [
            {"role": "system", "content": "Summarize the input into 3 bullet points and one headline."},
            {"role": "user", "content": text},
        ]
        result = backend.complete(
            messages,
            temperature=args.temperature,
            top_p=args.top_p,
            max_completion_tokens=args.max_completion_tokens,
            n=1,
        )
        rows.append(
            {
                "source": path.name,
                "summary": result.primary_text,
                "latency_seconds": round(result.latency_seconds, 3),
            }
        )
    total_runtime = time.perf_counter() - started
    if args.format == "csv":
        write_csv(args.output, rows)
    else:
        write_jsonl(args.output, rows)
    print(json.dumps({"records": rows, "total_runtime_seconds": round(total_runtime, 3)}, indent=2, ensure_ascii=True))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
