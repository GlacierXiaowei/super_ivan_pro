from __future__ import annotations

import os
from pathlib import Path


OVERRIDE_ENV = "SUPER_IVAN_WECHAT_AUTOMATION_ROOT"


def resolve_runtime_root(override: Path | None = None) -> Path:
    if override is not None:
        return Path(override)

    env_override = os.environ.get(OVERRIDE_ENV, "").strip()
    if env_override:
        return Path(env_override)

    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA is required for desktop service runtime root resolution")
    return Path(local_app_data) / "SuperIvanPro" / "wechat_automation"

