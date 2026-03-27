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
from utils.config import load_runtime_config
from utils.rag import budget_report, build_rag_messages, chunk_documents, retrieve_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Grounded document Q&A demo.")
    add_backend_args(parser)
    parser.add_argument("--docs-dir", default=str(REPO_ROOT / "data" / "docs"))
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--sequence-limit", type=int, default=8192)
    args = parser.parse_args()

    config = load_runtime_config(
        model_key=args.model_key,
        mode=args.mode,
        api_key=args.api_key,
        base_url=args.base_url,
        model_name=args.model_name,
        env_file=args.env_file,
    )
    chunks = chunk_documents(args.docs_dir)
    retrieved = retrieve_chunks(chunks, args.question, top_k=args.top_k)
    messages = build_rag_messages(args.question, retrieved)
    report = budget_report(
        messages,
        args.max_completion_tokens,
        sequence_limit=args.sequence_limit,
    )
    backend = build_backend(config)
    result = backend.complete(
        messages,
        temperature=args.temperature,
        top_p=args.top_p,
        max_completion_tokens=args.max_completion_tokens,
        n=1,
    )

    print("--- retrieved_chunks ---")
    for chunk in retrieved:
        print(f"{chunk.chunk_id} [{chunk.source}] score={chunk.score:.3f}")
    print("\n--- token_budget ---")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    if report["usage_ratio"] >= 0.85:
        print("warning=Estimated request is close to the configured sequence limit.")
    print("\n--- answer ---")
    print(result.primary_text)


if __name__ == "__main__":
    main()
