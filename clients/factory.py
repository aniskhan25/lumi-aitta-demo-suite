from __future__ import annotations

from clients.aitta_direct import AittaDirectBackend
from utils.config import RuntimeConfig


def build_backend(config: RuntimeConfig):
    return AittaDirectBackend(
        api_key=config.api_key,
        base_url=config.base_url,
        model_name=config.model_name,
        timeout=config.timeout_seconds,
    )
