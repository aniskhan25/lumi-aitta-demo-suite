from __future__ import annotations

import argparse
import json
from pathlib import Path


def pick_stable_concurrency(
    rows: list[dict[str, object]], *, p95_limit: float
) -> int | None:
    stable: list[int] = []
    for row in rows:
        summary = row["summary"]
        if (
            float(summary["failure_rate"]) == 0.0
            and float(summary["p95_latency_seconds"]) <= p95_limit
        ):
            stable.append(int(row["concurrency"]))
    return max(stable) if stable else None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize a benchmark matrix into capacity-oriented signals."
    )
    parser.add_argument("input", help="Path to benchmark_matrix.json")
    parser.add_argument("--interactive-p95-limit", type=float, default=3.0)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    baseline = payload["baseline"]["summary"]
    concurrency_rows = payload["concurrency_sweep"]
    token_rows = payload["token_sweep"]

    best_stable_concurrency = pick_stable_concurrency(
        concurrency_rows,
        p95_limit=args.interactive_p95_limit,
    )
    best_throughput_row = max(token_rows, key=lambda row: float(row["summary"]["completion_tokens_per_second"]))

    summary = {
        "model_name": payload["config"]["model_name"],
        "baseline_latency": {
            "avg_latency_seconds": float(baseline["avg_latency_seconds"]),
            "p50_latency_seconds": float(baseline["p50_latency_seconds"]),
            "p95_latency_seconds": float(baseline["p95_latency_seconds"]),
            "p99_latency_seconds": float(baseline["p99_latency_seconds"]),
        },
        "slow_request_rates": {
            "over_3s": float(baseline["slow_request_rates"]["over_3s"]),
            "over_10s": float(baseline["slow_request_rates"]["over_10s"]),
            "over_30s": float(baseline["slow_request_rates"]["over_30s"]),
        },
        "stable_concurrency_at_p95_limit": best_stable_concurrency,
        "interactive_p95_limit_seconds": args.interactive_p95_limit,
        "repeat_variability": {
            "baseline_p95_spread_seconds": float(payload["baseline"].get("repeat_spreads", {}).get("p95_latency_seconds", 0.0)),
            "baseline_avg_latency_spread_seconds": float(payload["baseline"].get("repeat_spreads", {}).get("avg_latency_seconds", 0.0)),
        },
        "best_token_throughput": {
            "max_completion_tokens": best_throughput_row["max_completion_tokens"],
            "completion_tokens_per_second": float(best_throughput_row["summary"]["completion_tokens_per_second"]),
            "avg_latency_seconds": float(best_throughput_row["summary"]["avg_latency_seconds"]),
        },
        "concurrency_sweep": [
            {
                "concurrency": row["concurrency"],
                "p95_latency_seconds": float(row["summary"]["p95_latency_seconds"]),
                "failure_rate": float(row["summary"]["failure_rate"]),
                "completion_tokens_per_second": float(row["summary"]["completion_tokens_per_second"]),
                "over_3s_rate": float(row["summary"]["slow_request_rates"]["over_3s"]),
                "over_10s_rate": float(row["summary"]["slow_request_rates"]["over_10s"]),
                "over_30s_rate": float(row["summary"]["slow_request_rates"]["over_30s"]),
                "p95_spread_seconds": float(row.get("repeat_spreads", {}).get("p95_latency_seconds", 0.0)),
            }
            for row in concurrency_rows
        ],
        "token_sweep": [
            {
                "max_completion_tokens": row["max_completion_tokens"],
                "avg_latency_seconds": float(row["summary"]["avg_latency_seconds"]),
                "completion_tokens_per_second": float(row["summary"]["completion_tokens_per_second"]),
                "avg_completion_tokens": float(row["summary"]["avg_completion_tokens"]),
                "over_3s_rate": float(row["summary"]["slow_request_rates"]["over_3s"]),
                "p95_spread_seconds": float(row.get("repeat_spreads", {}).get("p95_latency_seconds", 0.0)),
            }
            for row in token_rows
        ],
    }

    markdown_lines = [
        "# Benchmark Matrix Summary",
        "",
        f"- model_name: {summary['model_name']}",
        f"- baseline_avg_latency_seconds: {summary['baseline_latency']['avg_latency_seconds']}",
        f"- baseline_p95_latency_seconds: {summary['baseline_latency']['p95_latency_seconds']}",
        f"- baseline_over_3s_rate: {summary['slow_request_rates']['over_3s']}",
        f"- baseline_over_10s_rate: {summary['slow_request_rates']['over_10s']}",
        f"- baseline_over_30s_rate: {summary['slow_request_rates']['over_30s']}",
        f"- stable_concurrency_at_p95_limit: {summary['stable_concurrency_at_p95_limit']}",
        f"- baseline_p95_spread_seconds: {summary['repeat_variability']['baseline_p95_spread_seconds']}",
        f"- best_token_throughput_tokens_per_second: {summary['best_token_throughput']['completion_tokens_per_second']}",
        f"- best_token_throughput_max_completion_tokens: {summary['best_token_throughput']['max_completion_tokens']}",
        "",
        "## Concurrency Sweep",
        "",
    ]
    for row in summary["concurrency_sweep"]:
        markdown_lines.append(
            f"- concurrency={row['concurrency']}: "
            f"p95_latency_seconds={row['p95_latency_seconds']}, "
            f"failure_rate={row['failure_rate']}, "
            f"completion_tokens_per_second={row['completion_tokens_per_second']}, "
            f"over_3s_rate={row['over_3s_rate']}, "
            f"over_10s_rate={row['over_10s_rate']}, "
            f"over_30s_rate={row['over_30s_rate']}, "
            f"p95_spread_seconds={row['p95_spread_seconds']}"
        )
    markdown_lines.extend(["", "## Token Sweep", ""])
    for row in summary["token_sweep"]:
        markdown_lines.append(
            f"- max_completion_tokens={row['max_completion_tokens']}: "
            f"avg_latency_seconds={row['avg_latency_seconds']}, "
            f"completion_tokens_per_second={row['completion_tokens_per_second']}, "
            f"avg_completion_tokens={row['avg_completion_tokens']}, "
            f"over_3s_rate={row['over_3s_rate']}, "
            f"p95_spread_seconds={row['p95_spread_seconds']}"
        )

    result = {
        "summary": summary,
        "markdown": "\n".join(markdown_lines) + "\n",
    }

    if args.output:
        Path(args.output).write_text(result["markdown"], encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    print()
    print(result["markdown"])


if __name__ == "__main__":
    main()
