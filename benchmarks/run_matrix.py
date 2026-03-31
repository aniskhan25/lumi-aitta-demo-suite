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

from clients.aitta_direct import AittaDirectBackend
from utils.benchmarking import BenchmarkRecord, run_concurrent, summarize_records
from utils.cli import add_backend_args
from utils.config import load_runtime_config
from utils.files import write_json


def log_progress(message: str) -> None:
    print(message, flush=True)


def fail_fast_on_auth_errors(run: dict[str, object]) -> None:
    summary = run["summary"]
    if summary["successes"] > 0:
        return
    records = run["records"]
    auth_errors = [
        record["error"]
        for record in records
        if record["error"] and ("401" in record["error"] or "invalid_token" in record["error"])
    ]
    if auth_errors:
        raise RuntimeError(auth_errors[0])


def aggregate_run_summaries(summaries: list[dict[str, object]]) -> dict[str, object]:
    if len(summaries) == 1:
        return summaries[0]

    def values(key: str) -> list[float]:
        return [float(summary[key]) for summary in summaries]

    def summarize_metric(key: str) -> dict[str, float]:
        metric_values = values(key)
        return {
            "avg": round(sum(metric_values) / len(metric_values), 3),
            "min": round(min(metric_values), 3),
            "max": round(max(metric_values), 3),
        }

    def summarize_counts(group_key: str) -> dict[str, dict[str, float]]:
        keys = summaries[0][group_key].keys()
        aggregated: dict[str, dict[str, float]] = {}
        for key in keys:
            metric_values = [float(summary[group_key][key]) for summary in summaries]
            aggregated[key] = {
                "avg": round(sum(metric_values) / len(metric_values), 4),
                "min": round(min(metric_values), 4),
                "max": round(max(metric_values), 4),
            }
        return aggregated

    return {
        "requests": int(summaries[0]["requests"]),
        "successes": summarize_metric("successes"),
        "failures": summarize_metric("failures"),
        "failure_rate": summarize_metric("failure_rate"),
        "wall_time_seconds": summarize_metric("wall_time_seconds"),
        "avg_latency_seconds": summarize_metric("avg_latency_seconds"),
        "p50_latency_seconds": summarize_metric("p50_latency_seconds"),
        "p95_latency_seconds": summarize_metric("p95_latency_seconds"),
        "p99_latency_seconds": summarize_metric("p99_latency_seconds"),
        "total_completion_tokens": summarize_metric("total_completion_tokens"),
        "avg_completion_tokens": summarize_metric("avg_completion_tokens"),
        "completion_tokens_per_second": summarize_metric("completion_tokens_per_second"),
        "slow_request_counts": summarize_counts("slow_request_counts"),
        "slow_request_rates": summarize_counts("slow_request_rates"),
        "repeat_count": len(summaries),
    }


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


def execute_repeated_run(
    *,
    label: str,
    backend,
    prompt: str,
    requests: int,
    concurrency: int,
    temperature: float,
    top_p: float,
    max_completion_tokens: int,
    n: int,
    repeats: int,
) -> dict[str, object]:
    runs: list[dict[str, object]] = []
    for repeat_index in range(repeats):
        log_progress(
            f"starting {label}: repeat={repeat_index + 1}/{repeats}, "
            f"requests={requests}, concurrency={concurrency}, max_completion_tokens={max_completion_tokens}"
        )
        run = execute_run(
            backend=backend,
            prompt=prompt,
            requests=requests,
            concurrency=concurrency,
            temperature=temperature,
            top_p=top_p,
            max_completion_tokens=max_completion_tokens,
            n=n,
        )
        fail_fast_on_auth_errors(run)
        summary = run["summary"]
        log_progress(
            f"finished {label}: repeat={repeat_index + 1}/{repeats}, "
            f"p95={summary['p95_latency_seconds']}s, "
            f"failures={summary['failures']}, "
            f"over_10s={summary['slow_request_counts']['over_10s']}"
        )
        runs.append(
            {
                "repeat": repeat_index + 1,
                "summary": run["summary"],
            }
        )
    return {
        "summary": aggregate_run_summaries([run["summary"] for run in runs]),
        "runs": runs,
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
    parser.add_argument("--repeats", type=int, default=1, help="Repeat each matrix point this many times.")
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
    backend = AittaDirectBackend(
        api_key=config.api_key,
        base_url=config.base_url,
        model_name=config.model_name,
        timeout=config.timeout_seconds,
    )
    prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    log_progress(
        f"starting benchmark matrix: model={config.model_name}, requests={args.requests}, repeats={args.repeats}"
    )

    baseline = execute_repeated_run(
        label="baseline",
        backend=backend,
        prompt=prompt,
        requests=args.requests,
        concurrency=args.baseline_concurrency,
        temperature=args.temperature,
        top_p=args.top_p,
        max_completion_tokens=max(args.max_token_values),
        n=args.n,
        repeats=args.repeats,
    )

    concurrency_sweep: list[dict[str, object]] = []
    for concurrency in args.concurrency_values:
        run = execute_repeated_run(
            label=f"concurrency={concurrency}",
            backend=backend,
            prompt=prompt,
            requests=args.requests,
            concurrency=concurrency,
            temperature=args.temperature,
            top_p=args.top_p,
            max_completion_tokens=max(args.max_token_values),
            n=args.n,
            repeats=args.repeats,
        )
        concurrency_sweep.append(
            {
                "concurrency": concurrency,
                "summary": run["summary"],
                "runs": run["runs"],
            }
        )

    token_sweep: list[dict[str, object]] = []
    for max_tokens in args.max_token_values:
        run = execute_repeated_run(
            label=f"max_tokens={max_tokens}",
            backend=backend,
            prompt=prompt,
            requests=args.requests,
            concurrency=args.baseline_concurrency,
            temperature=args.temperature,
            top_p=args.top_p,
            max_completion_tokens=max_tokens,
            n=args.n,
            repeats=args.repeats,
        )
        token_sweep.append(
            {
                "max_completion_tokens": max_tokens,
                "summary": run["summary"],
                "runs": run["runs"],
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
            "repeats": args.repeats,
        },
        "baseline": {
            "concurrency": args.baseline_concurrency,
            "max_completion_tokens": max(args.max_token_values),
            "summary": baseline["summary"],
            "runs": baseline["runs"],
        },
        "concurrency_sweep": concurrency_sweep,
        "token_sweep": token_sweep,
    }
    write_json(args.output, payload)
    log_progress("benchmark matrix complete")
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
