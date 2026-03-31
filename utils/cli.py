from __future__ import annotations

import argparse


def add_backend_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--api-key", default=None, help="Explicit API key override.")
    parser.add_argument("--model", default=None, help="Model name override.")
    parser.add_argument("--base-url", default=None, help="Explicit base URL override.")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-completion-tokens", type=int, default=256)
