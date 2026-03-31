from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILES = (
    REPO_ROOT / "config" / "aitta.env",
    REPO_ROOT / ".env",
)

DEFAULT_MODEL = "LumiOpen/Poro-34B-chat"

@dataclass(slots=True)
class RuntimeConfig:
    model_name: str
    api_key: str
    base_url: str
    timeout_seconds: float = 120.0


def load_runtime_config(
    *,
    model_name: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> RuntimeConfig:
    for candidate in DEFAULT_ENV_FILES:
        load_env_file(candidate)

    resolved_model_name = (
        model_name
        or os.getenv("AITTA_MODEL")
        or DEFAULT_MODEL
    )

    resolved_api_key = api_key or os.getenv("AITTA_API_KEY", "")
    if not resolved_api_key:
        raise ValueError("No API key found. Set AITTA_API_KEY or pass --api-key.")

    resolved_base_url = base_url or os.getenv("AITTA_BASE_URL", "")
    if not resolved_base_url:
        raise ValueError("Set AITTA_BASE_URL or pass --base-url.")

    timeout_seconds = float(os.getenv("AITTA_REQUEST_TIMEOUT", "120"))
    return RuntimeConfig(
        model_name=resolved_model_name,
        api_key=resolved_api_key,
        base_url=resolved_base_url,
        timeout_seconds=timeout_seconds,
    )


def load_env_file(path: str | Path | None) -> None:
    if path is None:
        return
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        normalized_value = value.strip()
        if len(normalized_value) >= 2 and normalized_value[0] == normalized_value[-1] and normalized_value[0] in {'"', "'"}:
            normalized_value = normalized_value[1:-1]
        os.environ.setdefault(key.strip(), normalized_value)
