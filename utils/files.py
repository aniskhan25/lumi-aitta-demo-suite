from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable


def list_text_files(path: str | Path) -> list[Path]:
    base = Path(path)
    if base.is_file():
        return [base]
    return sorted(
        candidate
        for candidate in base.rglob("*")
        if candidate.is_file() and candidate.suffix.lower() in {".txt", ".md"}
    )


def read_documents(path: str | Path) -> list[tuple[Path, str]]:
    return [(item, item.read_text(encoding="utf-8")) for item in list_text_files(path)]


def ensure_parent(path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def write_json(path: str | Path, payload: object) -> None:
    output_path = ensure_parent(path)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def write_jsonl(path: str | Path, rows: Iterable[dict]) -> None:
    output_path = ensure_parent(path)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def write_csv(path: str | Path, rows: list[dict]) -> None:
    output_path = ensure_parent(path)
    if not rows:
        output_path.write_text("", encoding="utf-8")
        return
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
