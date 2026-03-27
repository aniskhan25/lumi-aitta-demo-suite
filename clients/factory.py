from __future__ import annotations

from clients.aitta_direct import AittaDirectBackend
from clients.aitta_discovery import AittaDiscoveryBackend
from utils.config import RuntimeConfig


def build_backend(config: RuntimeConfig):
    if config.use_discovery:
        return AittaDiscoveryBackend(
            api_root=config.api_root,
            api_key=config.api_key,
            model_name=config.model_name,
            timeout=config.timeout_seconds,
        )
    return AittaDirectBackend(
        api_key=config.api_key,
        base_url=config.base_url,
        model_name=config.model_name,
        timeout=config.timeout_seconds,
    )
