from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Rule, RuntimeConfig


def _load_structured_file(path: str | Path) -> Any:
    resolved = Path(path).resolve()
    text = resolved.read_text(encoding="utf-8")
    suffix = resolved.suffix.lower()
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "YAML config requested but PyYAML is not installed."
            ) from exc
        return yaml.safe_load(text)
    raise ValueError(f"Unsupported config format: {resolved}")


def load_runtime_config(path: str | Path) -> RuntimeConfig:
    payload = _load_structured_file(path)
    if not isinstance(payload, dict):
        raise ValueError("Runtime config must be a JSON/YAML object.")
    return RuntimeConfig.from_dict(payload)


def load_rules(path: str | Path) -> list[Rule]:
    payload = _load_structured_file(path)
    if not isinstance(payload, list):
        raise ValueError("Rules config must be a JSON/YAML array.")
    return [Rule.from_dict(item) for item in payload]
