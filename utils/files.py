from __future__ import annotations

import json
from pathlib import Path


def list_text_files(path: str | Path) -> list[Path]:
    base = Path(path)
    if base.is_file():
        return [base]
    return sorted(candidate for candidate in base.rglob("*") if candidate.is_file() and candidate.suffix.lower() in {".txt", ".md"})


def ensure_parent(path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def write_json(path: str | Path, payload: object) -> None:
    output_path = ensure_parent(path)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
