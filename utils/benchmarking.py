from __future__ import annotations

import time
import statistics
import concurrent.futures

from typing import Any, Callable
from dataclasses import dataclass


@dataclass(slots=True)
class BenchmarkRecord:
    index: int
    success: bool
    latency_seconds: float
    error: str | None
    usage: dict[str, Any] | None
    response_texts: list[str]
    started_at: float


SLOW_LATENCY_THRESHOLDS = (3.0, 10.0, 30.0)
SYSTEM_MESSAGE = "Answer accurately and concisely."


def run_concurrent(
    *,
    worker: Callable[[int], BenchmarkRecord],
    requests: int,
    concurrency: int,
) -> list[BenchmarkRecord]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(worker, index) for index in range(requests)]
        return [future.result() for future in concurrent.futures.as_completed(futures)]


def make_chat_worker(
    *,
    backend: Any,
    prompt: str,
    temperature: float,
    top_p: float,
    max_completion_tokens: int,
    n: int,
) -> Callable[[int], BenchmarkRecord]:
    def worker(index: int) -> BenchmarkRecord:
        started_at = time.time()
        messages = [
            {"role": "system", "content": SYSTEM_MESSAGE},
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

    return worker


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    
    position = (len(values) - 1) * pct
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower

    return values[lower] * (1 - weight) + values[upper] * weight


def summarize_records(records: list[BenchmarkRecord]) -> dict[str, Any]:
    latencies = [record.latency_seconds for record in records if record.success]
    failures = [record for record in records if not record.success]

    completion_tokens = [
        int(record.usage.get("completion_tokens", 0))
        for record in records
        if record.usage
    ]

    started = min((record.started_at for record in records), default=time.time())
    finished = max((record.started_at + record.latency_seconds for record in records), default=started)
    wall_time = finished - started

    slow_request_counts = {
        f"over_{int(threshold)}s": sum(1 for latency in latencies if latency > threshold)
        for threshold in SLOW_LATENCY_THRESHOLDS
    }

    summary = {
        "requests": len(records),
        "successes": len(records) - len(failures),
        "failures": len(failures),
        "failure_rate": round(len(failures) / len(records), 4) if records else 0.0,
        "wall_time_seconds": round(wall_time, 3),
        "avg_latency_seconds": round(statistics.mean(latencies), 3) if latencies else 0.0,
        "p50_latency_seconds": round(percentile(latencies, 0.50), 3),
        "p95_latency_seconds": round(percentile(latencies, 0.95), 3),
        "p99_latency_seconds": round(percentile(latencies, 0.99), 3),
        "total_completion_tokens": sum(completion_tokens),
        "avg_completion_tokens": round(statistics.mean(completion_tokens), 1) if completion_tokens else 0.0,
        "completion_tokens_per_second": round(sum(completion_tokens) / wall_time, 3) if wall_time and completion_tokens else 0.0,
    }

    summary["slow_request_counts"] = slow_request_counts
    summary["slow_request_rates"] = {
        key: round(value / len(records), 4) if records else 0.0
        for key, value in slow_request_counts.items()
    }
    
    return summary
