from __future__ import annotations

import importlib
import inspect
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
        model = AittaDiscoveryBackend._find_model(client, model_name)
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
        candidate_names = ("AittaClient", "Client")
        for name in candidate_names:
            cls = getattr(module, name, None)
            if cls is None:
                continue
            for kwargs in (
                {"base_url": api_root, "api_key": api_key},
                {"api_root": api_root, "api_key": api_key},
                {"url": api_root, "api_key": api_key},
                {"base_url": api_root, "token": api_key},
                {"api_root": api_root, "token": api_key},
            ):
                try:
                    return cls(**AittaDiscoveryBackend._filter_kwargs(cls, kwargs))
                except TypeError:
                    continue
        raise RuntimeError("Could not construct an aitta-client discovery client.")

    @staticmethod
    def _find_model(client: Any, model_name: str) -> Any:
        direct_candidates = (
            ("get_model", (model_name,)),
            ("model", (model_name,)),
            ("get", (model_name,)),
        )
        for method_name, args in direct_candidates:
            method = getattr(client, method_name, None)
            if callable(method):
                try:
                    return method(*args)
                except TypeError:
                    continue

        models_attr = getattr(client, "models", None)
        if models_attr is not None:
            nested_candidates = (
                ("get", (model_name,)),
                ("retrieve", (model_name,)),
                ("by_name", (model_name,)),
                ("find", (model_name,)),
            )
            for method_name, args in nested_candidates:
                method = getattr(models_attr, method_name, None)
                if callable(method):
                    try:
                        return method(*args)
                    except TypeError:
                        continue
            if callable(models_attr):
                collection = models_attr()
            else:
                collection = models_attr
            matched = AittaDiscoveryBackend._scan_collection(collection, model_name)
            if matched is not None:
                return matched

        raise RuntimeError(
            "Could not find the requested model through aitta-client discovery. "
            "Update clients/aitta_discovery.py to match the installed client API."
        )

    @staticmethod
    def _scan_collection(collection: Any, model_name: str) -> Any | None:
        if isinstance(collection, dict):
            if model_name in collection:
                return collection[model_name]
            collection = collection.values()
        if isinstance(collection, (list, tuple, set)):
            for item in collection:
                candidate_name = AittaDiscoveryBackend._extract_attr(
                    item,
                    ("name", "model_name", "id"),
                )
                if candidate_name == model_name:
                    return item
        return None

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

    @staticmethod
    def _filter_kwargs(callable_obj: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
        try:
            params = inspect.signature(callable_obj).parameters
        except (TypeError, ValueError):
            return kwargs
        return {key: value for key, value in kwargs.items() if key in params}
