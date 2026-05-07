from __future__ import annotations

import json
import os
import shutil
from pathlib import Path


OVERRIDE_ENV = "SUPER_IVAN_WECHAT_AUTOMATION_ROOT"
DEFAULT_APP_DATA_FOLDER = "SuperIvanPro"
DEFAULT_RUNTIME_FOLDER = "wechat_automation"


def resolve_repo_root(override: Path | None = None) -> Path:
    if override is not None:
        return Path(override)
    return Path(__file__).resolve().parents[1]


def resolve_runtime_root(override: Path | None = None) -> Path:
    if override is not None:
        return Path(override)

    env_override = os.environ.get(OVERRIDE_ENV, "").strip()
    if env_override:
        return Path(env_override)

    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA is required for desktop service runtime root resolution")
    return Path(local_app_data) / DEFAULT_APP_DATA_FOLDER / DEFAULT_RUNTIME_FOLDER


def ensure_runtime_files(runtime_root: Path, repo_root: Path) -> dict[str, Path]:
    resolved_runtime_root = Path(runtime_root)
    resolved_repo_root = Path(repo_root)
    runtime_config_path = resolved_runtime_root / "config" / "runtime.local.json"
    rules_path = resolved_runtime_root / "config" / "rules.local.json"
    arm_state_path = resolved_runtime_root / "config" / "arm_state.local.json"

    source_runtime_path = _first_existing(
        [
            resolved_repo_root / "config" / "runtime.local.json",
            resolved_repo_root / "config" / "runtime.example.json",
        ]
    )
    source_rules_path = _first_existing(
        [
            resolved_repo_root / "config" / "rules.local.json",
            resolved_repo_root / "config" / "rules.example.json",
        ]
    )
    source_arm_state_path = _first_existing(
        [
            resolved_repo_root / "config" / "arm_state.local.json",
            resolved_repo_root / "config" / "arm_state.example.json",
        ]
    )

    rules_path.parent.mkdir(parents=True, exist_ok=True)
    (resolved_runtime_root / "logs").mkdir(parents=True, exist_ok=True)

    if not rules_path.exists():
        if source_rules_path is not None:
            shutil.copyfile(source_rules_path, rules_path)
        else:
            rules_path.write_text("[]", encoding="utf-8")

    if not arm_state_path.exists():
        if source_arm_state_path is not None:
            shutil.copyfile(source_arm_state_path, arm_state_path)
        else:
            arm_state_path.write_text(
                json.dumps(
                    {
                        "enabled": False,
                        "mode": "armed_current_chat",
                        "max_triggers": 1,
                        "triggers_sent": 0,
                        "remaining_triggers": 1,
                        "reason": "not_armed",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

    existing_runtime_payload: dict[str, object] = {}
    if runtime_config_path.exists():
        try:
            loaded = json.loads(runtime_config_path.read_text(encoding="utf-8-sig"))
            if isinstance(loaded, dict):
                existing_runtime_payload = loaded
        except json.JSONDecodeError:
            existing_runtime_payload = {}
    elif source_runtime_path is not None:
        loaded = json.loads(source_runtime_path.read_text(encoding="utf-8-sig"))
        if isinstance(loaded, dict):
            existing_runtime_payload = loaded

    runtime_payload = _normalize_runtime_payload(
        payload=existing_runtime_payload,
        runtime_root=resolved_runtime_root,
        arm_state_path=arm_state_path,
        repo_root=resolved_repo_root,
    )
    runtime_config_path.write_text(
        json.dumps(runtime_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "runtime_root": resolved_runtime_root,
        "runtime": runtime_config_path,
        "rules": rules_path,
        "arm_state": arm_state_path,
        "logs": resolved_runtime_root / "logs",
    }


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _normalize_runtime_payload(
    payload: dict[str, object],
    runtime_root: Path,
    arm_state_path: Path,
    repo_root: Path,
) -> dict[str, object]:
    runtime_payload = dict(payload)
    runtime_payload["arm_state_path"] = str(arm_state_path)
    runtime_payload["log_dir"] = str((runtime_root / "logs"))
    packaged_root = resolve_packaged_root(repo_root)
    wechat_decrypt_root = str(runtime_payload.get("wechat_decrypt_root", "") or "").strip()
    if not wechat_decrypt_root:
        bundled_wechat_decrypt_root = (
            packaged_root / "runtime" / "wechat-decrypt"
            if packaged_root is not None and (packaged_root / "runtime" / "wechat-decrypt" / "main.py").exists()
            else None
        )
        if bundled_wechat_decrypt_root is not None:
            runtime_payload["wechat_decrypt_root"] = str(bundled_wechat_decrypt_root)
    if packaged_root is not None:
        sender_backend = str(runtime_payload.get("sender_backend", "") or "").strip()
        if not sender_backend:
            runtime_payload["sender_backend"] = "current_chat"
        if "dry_run" not in runtime_payload:
            runtime_payload["dry_run"] = False
    return runtime_payload


def resolve_packaged_wechat_decrypt_root(repo_root: Path) -> Path | None:
    package_root = resolve_packaged_root(repo_root)
    if package_root is None:
        return None

    bundled_root = package_root / "runtime" / "wechat-decrypt"
    if (bundled_root / "main.py").exists():
        return bundled_root
    return None


def resolve_packaged_root(repo_root: Path) -> Path | None:
    resolved_repo_root = Path(repo_root)
    for candidate in [resolved_repo_root, *resolved_repo_root.parents]:
        if (candidate / "super_ivan_pro.exe").exists() or (candidate / "flutter_windows.dll").exists():
            return candidate
    return None
