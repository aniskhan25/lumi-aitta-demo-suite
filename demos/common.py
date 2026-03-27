from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def add_backend_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--env-file", default=None, help="Optional env file to load before config resolution.")
    parser.add_argument("--model-key", default=None, help="Model alias from config/models.yaml.")
    parser.add_argument(
        "--mode",
        choices=("discovery", "direct"),
        default=None,
        help="Override the configured backend mode.",
    )
    parser.add_argument("--model-name", default=None, help="Explicit model name override.")
    parser.add_argument("--api-key", default=None, help="Explicit API key override.")
    parser.add_argument("--base-url", default=None, help="Explicit direct-mode base URL override.")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-completion-tokens", type=int, default=256)
