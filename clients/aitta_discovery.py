from __future__ import annotations

import importlib
from typing import Any

from clients.aitta_direct import AittaDirectBackend


class AittaDiscoveryBackend(AittaDirectBackend):
    backend_name = "aitta_discovery"

    def __init__(
        self,
        *,
        api_root: str,
        api_key: str,
        model_name: str,
        timeout: float = 120.0,
    ) -> None:
        self.api_root = api_root
        self.discovery_metadata = self._resolve_model_metadata(
            api_root=api_root,
            api_key=api_key,
            model_name=model_name,
        )
        base_url = self.discovery_metadata["openai_api_url"]
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            timeout=timeout,
        )

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any):
        result = super().complete(messages, **kwargs)
        result.metadata.update(self.discovery_metadata)
        return result

    @staticmethod
    def _resolve_model_metadata(*, api_root: str, api_key: str, model_name: str) -> dict[str, Any]:
        try:
            module = importlib.import_module("aitta_client")
        except ImportError as exc:
            raise RuntimeError(
                "Discovery mode requires the optional 'aitta-client' dependency."
            ) from exc

        client = AittaDiscoveryBackend._build_client(module, api_root=api_root, api_key=api_key)
        model = AittaDiscoveryBackend._load_model(module, client, model_name)
        openai_api_url = AittaDiscoveryBackend._extract_attr(
            model,
            ("openai_api_url", "openaiUrl", "url"),
        )
        if not openai_api_url:
            raise RuntimeError(
                f"Discovered model '{model_name}' does not expose an OpenAI API URL."
            )

        metadata = {
            "openai_api_url": openai_api_url,
            "description": AittaDiscoveryBackend._extract_attr(
                model,
                ("description", "summary", "details"),
            ),
            "id": AittaDiscoveryBackend._extract_attr(model, ("id", "name", "model_name")),
            "raw_model": AittaDiscoveryBackend._serialize_object(model),
        }
        return metadata

    @staticmethod
    def _build_client(module: Any, *, api_root: str, api_key: str) -> Any:
        client_cls = getattr(module, "Client", None)
        token_source_cls = getattr(module, "StaticAccessTokenSource", None)
        if client_cls is None or token_source_cls is None:
            raise RuntimeError(
                "Installed aitta-client does not expose Client and StaticAccessTokenSource."
            )

        try:
            token_source = token_source_cls(api_key)
            return client_cls(api_root, token_source)
        except TypeError as exc:
            raise RuntimeError(
                "Could not construct an aitta-client discovery client using "
                "Client(api_root, StaticAccessTokenSource(api_key))."
            ) from exc

    @staticmethod
    def _load_model(module: Any, client: Any, model_name: str) -> Any:
        model_cls = getattr(module, "Model", None)
        if model_cls is None:
            raise RuntimeError("Installed aitta-client does not expose Model.")
        load_method = getattr(model_cls, "load", None)
        if not callable(load_method):
            raise RuntimeError("Installed aitta-client Model does not expose load().")
        try:
            return load_method(model_name, client)
        except Exception as exc:
            raise RuntimeError(
                f"Could not load model '{model_name}' through aitta-client discovery."
            ) from exc

    @staticmethod
    def _extract_attr(value: Any, names: tuple[str, ...]) -> Any | None:
        if isinstance(value, dict):
            for name in names:
                if name in value:
                    return value[name]
            return None
        for name in names:
            if hasattr(value, name):
                return getattr(value, name)
        return None

    @staticmethod
    def _serialize_object(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        for method_name in ("model_dump", "dict", "to_dict"):
            method = getattr(value, method_name, None)
            if callable(method):
                payload = method()
                if isinstance(payload, dict):
                    return payload
        result: dict[str, Any] = {}
        for name in dir(value):
            if name.startswith("_"):
                continue
            try:
                attr = getattr(value, name)
            except Exception:
                continue
            if callable(attr):
                continue
            if isinstance(attr, (str, int, float, bool, dict, list, type(None))):
                result[name] = attr
        return result
