from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def add_backend_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--discovery", action="store_true", help="Use aitta-client discovery instead of a direct base URL.")
    parser.add_argument("--api-root", default=None, help="Aitta discovery root. Only needed with --discovery.")
    parser.add_argument("--api-key", default=None, help="Explicit API key override.")
    parser.add_argument("--model", default=None, help="Model name override.")
    parser.add_argument("--base-url", default=None, help="Explicit direct-mode base URL override.")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-completion-tokens", type=int, default=256)
