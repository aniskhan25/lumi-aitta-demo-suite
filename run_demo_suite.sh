#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

python demos/smoke_test.py "$@"
python demos/rag_demo.py --question "Why is client-managed memory necessary?" "$@"
python demos/extraction_demo.py "$@"
python demos/multiturn_demo.py "$@"
python demos/reasoning_candidates_demo.py "$@"
