from __future__ import annotations

import argparse
import json
from pathlib import Path


def render_benchmark_section(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    lines = [f"## {path.stem.replace('_', ' ').title()}", ""]
    if "summary" in payload:
        for key, value in payload["summary"].items():
            lines.append(f"- {key}: {value}")
    if "results" in payload:
        for row in payload["results"]:
            lines.append(
                f"- n={row['n']}: wall_time_seconds={row['wall_time_seconds']}, "
                f"avg_latency_seconds={row['avg_latency_seconds']}, "
                f"candidate_diversity_avg={row['candidate_diversity_avg']}, "
                f"normalized_agreement_avg={row['normalized_agreement_avg']}, "
                f"failure_rate={row['failure_rate']}"
            )
    lines.append("")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Markdown capability report.")
    parser.add_argument(
        "--benchmark-files",
        nargs="*",
        default=[],
        help="One or more benchmark JSON files.",
    )
    parser.add_argument(
        "--demo-files",
        nargs="*",
        default=[],
        help="Optional demo artifact files to reference.",
    )
    parser.add_argument(
        "--output",
        default="reports/example_outputs/aitta_capability_report.md",
    )
    args = parser.parse_args()

    lines = [
        "# Aitta Capability Report",
        "",
        "## Supported Behaviors",
        "",
        "- OpenAI-compatible chat completions transport.",
        "- Direct URL backend selection by default, with optional discovery.",
        "- Client-managed conversation history through `messages`.",
        "- Multi-candidate completions through `n`.",
        "- Direct smoke-test streaming support.",
        "",
        "## Benchmarks",
        "",
    ]
    for benchmark_file in args.benchmark_files:
        lines.extend(render_benchmark_section(Path(benchmark_file)))

    lines.extend(
        [
            "## Demo Artifacts",
            "",
        ]
    )
    if args.demo_files:
        for demo_file in args.demo_files:
            lines.append(f"- {demo_file}")
    else:
        lines.append("- No demo artifact files were supplied.")

    lines.extend(
        [
            "",
            "## Caveats",
            "",
            "- Benchmark scripts currently measure whole-response latency rather than token-stream cadence.",
            "- Memory continuity is handled client-side by rebuilding `messages` on each turn.",
            "- Token budgeting in the demos uses heuristics and should be validated against the target model.",
            "",
        ]
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
