from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from utils.env import load_env_file

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILES = (
    REPO_ROOT / "config" / "aitta.env",
    REPO_ROOT / ".env",
)
MODELS_PATH = REPO_ROOT / "config" / "models.yaml"


@dataclass(slots=True)
class RuntimeConfig:
    model_key: str | None
    model_name: str
    api_key: str
    api_root: str
    base_url: str
    use_discovery: bool
    supports_stream: bool
    notes: str
    timeout_seconds: float = 120.0


def load_runtime_config(
    *,
    model_key: str | None = None,
    mode: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
    env_file: str | None = None,
) -> RuntimeConfig:
    if env_file:
        load_env_file(env_file)
    else:
        for candidate in DEFAULT_ENV_FILES:
            load_env_file(candidate)

    models = load_models_config()
    selected_key = model_key or os.getenv("AITTA_MODEL_ALIAS")
    model_entry = models.get(selected_key, {}) if selected_key else {}

    resolved_model_name = (
        model_name
        or model_entry.get("model_name")
        or os.getenv("AITTA_MODEL_NAME")
    )
    if not resolved_model_name:
        raise ValueError("No Aitta model name configured.")

    token_env = model_entry.get("token_env", "AITTA_API_KEY")
    resolved_api_key = api_key or os.getenv(token_env) or os.getenv("AITTA_API_KEY", "")
    if not resolved_api_key:
        raise ValueError(
            f"No API key found. Expected {token_env} or AITTA_API_KEY in the environment."
        )

    api_root = os.getenv("AITTA_API_ROOT", "https://api-staging-aitta.2.rahtiapp.fi")
    entry_base_env = model_entry.get("base_url_env")
    resolved_base_url = base_url or (
        os.getenv(entry_base_env) if entry_base_env else None
    ) or os.getenv("AITTA_BASE_URL", "")
    default_use_discovery = bool(model_entry.get("use_discovery", False))
    env_use_discovery = parse_bool(os.getenv("AITTA_USE_DISCOVERY"))
    resolved_use_discovery = default_use_discovery if env_use_discovery is None else env_use_discovery
    if mode == "direct":
        resolved_use_discovery = False
    elif mode == "discovery":
        resolved_use_discovery = True

    if not resolved_use_discovery and not resolved_base_url:
        raise ValueError("Direct mode requires AITTA_BASE_URL or an explicit --base-url.")

    timeout_seconds = float(os.getenv("AITTA_REQUEST_TIMEOUT", "120"))
    return RuntimeConfig(
        model_key=selected_key,
        model_name=resolved_model_name,
        api_key=resolved_api_key,
        api_root=api_root,
        base_url=resolved_base_url,
        use_discovery=resolved_use_discovery,
        supports_stream=bool(model_entry.get("supports_stream", False)),
        notes=model_entry.get("notes", ""),
        timeout_seconds=timeout_seconds,
    )


def load_models_config(path: Path = MODELS_PATH) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError("config/models.yaml must contain a mapping of model aliases.")
    return payload


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None
