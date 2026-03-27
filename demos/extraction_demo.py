from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from demos.common import REPO_ROOT, add_backend_args
from clients.factory import build_backend
from utils.chat import maybe_parse_json
from utils.config import load_runtime_config
from utils.files import read_documents, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Structured extraction demo.")
    add_backend_args(parser)
    parser.add_argument("--input-dir", default=str(REPO_ROOT / "data" / "extraction_samples"))
    parser.add_argument("--output", default=str(REPO_ROOT / "reports" / "example_outputs" / "extraction_results.json"))
    args = parser.parse_args()

    config = load_runtime_config(
        model_name=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        use_discovery=args.discovery,
        api_root=args.api_root,
    )
    backend = build_backend(config)
    rows: list[dict[str, object]] = []
    for path, text in read_documents(args.input_dir):
        messages = [
            {
                "role": "system",
                "content": (
                    "Extract structured fields from the note. "
                    "Return strict JSON with keys: title, summary, action_items, owner, due_date."
                ),
            },
            {"role": "user", "content": text},
        ]
        result = backend.complete(
            messages,
            temperature=args.temperature,
            top_p=args.top_p,
            max_completion_tokens=args.max_completion_tokens,
            n=1,
        )
        parsed = maybe_parse_json(result.primary_text)
        rows.append(
            {
                "source": path.name,
                "parsed": parsed,
                "raw_response": result.primary_text if parsed is None else None,
                "latency_seconds": round(result.latency_seconds, 3),
            }
        )
    write_json(args.output, rows)
    print(json.dumps(rows, indent=2, ensure_ascii=True))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
