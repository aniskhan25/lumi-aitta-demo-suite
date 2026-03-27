from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize benchmark JSON into Markdown.")
    parser.add_argument("input", help="Path to a benchmark JSON file.")
    parser.add_argument("--output", default=None, help="Optional Markdown output path.")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    lines: list[str] = ["# Benchmark Summary", ""]
    if "summary" in payload:
        lines.append("## OpenAI-Compatible Benchmark")
        for key, value in payload["summary"].items():
            lines.append(f"- {key}: {value}")
    if "results" in payload:
        lines.append("## Reasoning Benchmark")
        for result in payload["results"]:
            lines.append(
                f"- n={result['n']}: avg_latency_seconds={result['avg_latency_seconds']}, "
                f"candidate_diversity_avg={result['candidate_diversity_avg']}, "
                f"normalized_agreement_avg={result['normalized_agreement_avg']}, "
                f"failure_rate={result['failure_rate']}"
            )
    markdown = "\n".join(lines) + "\n"
    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
