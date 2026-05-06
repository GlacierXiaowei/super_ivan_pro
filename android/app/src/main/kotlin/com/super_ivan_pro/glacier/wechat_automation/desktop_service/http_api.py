from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse
import urllib.request

from core.arm_state import ArmStateStore
from core.config_loader import load_runtime_config
from core.history_sender_search import HistorySenderCandidate, search_history_senders
from core.models import MessageEvent, RuntimeConfig
from core.watcher_adapter import WechatDecryptHistoryWatcher

from .config_paths import ensure_runtime_files, resolve_repo_root, resolve_runtime_root
from .state_store import DesktopStateStore


RUNTIME_MODE_PROFILES: dict[str, dict[str, Any]] = {
    "normal": {
        "poll_interval_ms": 300,
        "history_limit": 200,
        "inter_message_delay_ms": 180,
        "retry_count": 1,
        "current_chat_fast_send": False,
    },
    "rapid": {
        "poll_interval_ms": 20,
        "history_limit": 50,
        "inter_message_delay_ms": 0,
        "retry_count": 0,
        "current_chat_fast_send": True,
    },
}


def _event_to_payload(event: MessageEvent) -> dict[str, object]:
    return {
        "seq": event.seq,
        "timestamp": event.timestamp,
        "talker": event.talker,
        "chat_name": event.display_talker,
        "talker_name": event.display_talker,
        "sender": event.sender,
        "sender_name": event.display_sender,
        "is_chat_room": event.is_chat_room,
        "chat_scope": "group" if event.is_chat_room else "private",
        "type": event.message_type.value,
        "content": event.content,
        "raw": event.raw,
    }


def _log_to_payload(source: str, message: str) -> dict[str, str]:
    return {
        "source": source,
        "message": message,
    }


def _history_sender_to_payload(candidate: object) -> dict[str, object]:
    if isinstance(candidate, HistorySenderCandidate):
        return candidate.to_dict()
    if isinstance(candidate, dict):
        return {
            "sender": str(candidate.get("sender", "")),
            "sender_name": str(candidate.get("sender_name", "")),
            "last_timestamp": int(candidate.get("last_timestamp", 0) or 0),
            "last_content": str(candidate.get("last_content", "")),
            "message_count": int(candidate.get("message_count", 0) or 0),
        }
    return {
        "sender": "",
        "sender_name": "",
        "last_timestamp": 0,
        "last_content": "",
        "message_count": 0,
    }


class BotProcessManager:
    def __init__(
        self,
        repo_root: Path,
        runtime_root: Path,
        popen_factory: Callable[..., Any] = subprocess.Popen,
        python_executable: str = sys.executable,
    ) -> None:
        self._repo_root = Path(repo_root)
        self._runtime_root = Path(runtime_root)
        self._popen_factory = popen_factory
        self._python_executable = python_executable
        self._process: Any | None = None
        self._stdout_handle: Any | None = None
        self._stderr_handle: Any | None = None

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self, runtime_path: Path, rules_path: Path) -> bool:
        if self.is_running():
            return False

        self._cleanup_handles()
        logs_dir = self._runtime_root / "logs" / "live_bot"
        logs_dir.mkdir(parents=True, exist_ok=True)
        self._stdout_handle = (logs_dir / "stdout.log").open("a", encoding="utf-8")
        self._stderr_handle = (logs_dir / "stderr.log").open("a", encoding="utf-8")

        command = [
            self._python_executable,
            str((self._repo_root / "scripts" / "run_bot.py")),
            "--runtime",
            str(runtime_path),
            "--rules",
            str(rules_path),
            "--live",
        ]
        self._process = self._popen_factory(
            command,
            cwd=str(self._repo_root),
            stdout=self._stdout_handle,
            stderr=self._stderr_handle,
        )
        return True

    def stop(self) -> bool:
        if not self.is_running():
            self._process = None
            self._cleanup_handles()
            return False

        assert self._process is not None
        self._process.terminate()
        try:
            self._process.wait(timeout=5)
        except Exception:
            self._process.kill()
            self._process.wait(timeout=2)
        finally:
            self._process = None
            self._cleanup_handles()
        return True

    def restart(self, runtime_path: Path, rules_path: Path) -> bool:
        was_running = self.is_running()
        if was_running:
            self.stop()
        self.start(runtime_path, rules_path)
        return was_running

    def _cleanup_handles(self) -> None:
        if self._stdout_handle is not None:
            self._stdout_handle.close()
        if self._stderr_handle is not None:
            self._stderr_handle.close()
        self._stdout_handle = None
        self._stderr_handle = None


class WechatDecryptProcessManager:
    def __init__(
        self,
        runtime_root: Path,
        popen_factory: Callable[..., Any] = subprocess.Popen,
        python_executable: str = sys.executable,
    ) -> None:
        self._runtime_root = Path(runtime_root)
        self._popen_factory = popen_factory
        self._python_executable = python_executable
        self._process: Any | None = None
        self._stdout_handle: Any | None = None
        self._stderr_handle: Any | None = None

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self, source_root: Path) -> bool:
        if self.is_running():
            return False

        script_path = source_root / "main.py"
        if not script_path.exists():
            return False

        self._cleanup_handles()
        logs_dir = self._runtime_root / "logs" / "wechat_decrypt"
        logs_dir.mkdir(parents=True, exist_ok=True)
        self._stdout_handle = (logs_dir / "stdout.log").open("a", encoding="utf-8")
        self._stderr_handle = (logs_dir / "stderr.log").open("a", encoding="utf-8")

        command = [self._python_executable, "main.py"]
        self._process = self._popen_factory(
            command,
            cwd=str(source_root),
            stdout=self._stdout_handle,
            stderr=self._stderr_handle,
        )
        return True

    def stop(self) -> bool:
        if not self.is_running():
            self._process = None
            self._cleanup_handles()
            return False

        assert self._process is not None
        self._process.terminate()
        try:
            self._process.wait(timeout=5)
        except Exception:
            self._process.kill()
            self._process.wait(timeout=2)
        finally:
            self._process = None
            self._cleanup_handles()
        return True

    def _cleanup_handles(self) -> None:
        if self._stdout_handle is not None:
            self._stdout_handle.close()
        if self._stderr_handle is not None:
            self._stderr_handle.close()
        self._stdout_handle = None
        self._stderr_handle = None


class DesktopServiceApp:
    def __init__(
        self,
        runtime_root: Path,
        repo_root: Path,
        watcher_factory: Callable[[RuntimeConfig], object] = WechatDecryptHistoryWatcher,
        popen_factory: Callable[..., Any] = subprocess.Popen,
        python_executable: str = sys.executable,
        source_health_check: Callable[[RuntimeConfig], bool] | None = None,
        history_sender_searcher: Callable[[Path, str, str, int], list[object]] = search_history_senders,
    ) -> None:
        self._runtime_root = Path(runtime_root)
        self._repo_root = Path(repo_root)
        self._paths = ensure_runtime_files(self._runtime_root, self._repo_root)
        self._runtime_config_path = self._paths["runtime"]
        self._rules_path = self._paths["rules"]
        self._arm_state_path = self._paths["arm_state"]
        self._store = DesktopStateStore(self._runtime_root)
        self._watcher_factory = watcher_factory
        self._source_health_check = source_health_check or _default_source_health_check
        self._history_sender_searcher = history_sender_searcher
        self._last_watcher_error = ""
        self._process_manager = BotProcessManager(
            repo_root=self._repo_root,
            runtime_root=self._runtime_root,
            popen_factory=popen_factory,
            python_executable=python_executable,
        )
        self._source_process_manager = WechatDecryptProcessManager(
            runtime_root=self._runtime_root,
            popen_factory=popen_factory,
            python_executable=python_executable,
        )

    def handle_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        normalized_method = method.upper()
        parsed = urlparse(path)
        normalized_path = parsed.path
        query = parse_qs(parsed.query)

        if normalized_method == "GET" and normalized_path == "/status":
            return HTTPStatus.OK, self._build_status(limit=20)

        if normalized_method == "POST" and normalized_path == "/services/start":
            self._apply_runtime_mode_profile(str(self._store.load().get("mode", "normal")))
            runtime = load_runtime_config(self._runtime_config_path)
            if self._ensure_source_available(runtime):
                self._process_manager.start(self._runtime_config_path, self._rules_path)
            return HTTPStatus.OK, self._build_status(limit=20, refresh_events=False)

        if normalized_method == "POST" and normalized_path == "/services/restart":
            self._apply_runtime_mode_profile(str(self._store.load().get("mode", "normal")))
            runtime = load_runtime_config(self._runtime_config_path)
            if self._ensure_source_available(runtime):
                self._process_manager.restart(self._runtime_config_path, self._rules_path)
            return HTTPStatus.OK, self._build_status(limit=20, refresh_events=False)

        if normalized_method == "POST" and normalized_path == "/services/stop":
            self._process_manager.stop()
            self._source_process_manager.stop()
            return HTTPStatus.OK, self._build_status(limit=20, refresh_events=False)

        if normalized_method == "POST" and normalized_path == "/targets/active":
            body = payload if isinstance(payload, dict) else {}
            required = ("talker", "display_name", "is_group")
            missing = [key for key in required if key not in body]
            if missing:
                return HTTPStatus.BAD_REQUEST, {
                    "ok": False,
                    "error": f"missing required fields: {', '.join(missing)}",
                }

            state = self._store.load()
            state["active_target"] = {
                "talker": str(body["talker"]),
                "display_name": str(body["display_name"]),
                "is_group": bool(body["is_group"]),
            }
            self._store.save(state)
            self._sync_desktop_rule_target(
                talker=str(body["talker"]),
                is_group=bool(body["is_group"]),
            )
            if self._process_manager.is_running():
                self._process_manager.restart(self._runtime_config_path, self._rules_path)
            return HTTPStatus.OK, self._build_status(limit=20, refresh_events=False)

        if normalized_method == "GET" and normalized_path == "/rules":
            return HTTPStatus.OK, {"rules": self._read_rules()}

        if normalized_method == "POST" and normalized_path == "/rules":
            body = payload if isinstance(payload, dict) else {}
            rules = body.get("rules", payload)
            if not isinstance(rules, list):
                return HTTPStatus.BAD_REQUEST, {
                    "ok": False,
                    "error": "rules payload must be a list",
                }
            self._rules_path.write_text(
                json.dumps(rules, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            if self._process_manager.is_running():
                self._process_manager.restart(self._runtime_config_path, self._rules_path)
            return HTTPStatus.OK, self._build_status(limit=20, refresh_events=False)

        if normalized_method == "GET" and normalized_path == "/arm-state":
            return HTTPStatus.OK, self._arm_state_payload()

        if normalized_method == "POST" and normalized_path == "/arm-state":
            if not isinstance(payload, dict):
                return HTTPStatus.BAD_REQUEST, {
                    "ok": False,
                    "error": "arm-state payload must be an object",
                }
            body = payload

            store = ArmStateStore(self._arm_state_path)
            enabled = bool(body.get("enabled", False))
            if enabled:
                raw_max = body.get("max_triggers", 1)
                max_triggers = int(raw_max)
                store.arm(max_triggers=max_triggers)
            else:
                store.disarm(reason="manual_disarm")
            return HTTPStatus.OK, self._build_status(limit=20, refresh_events=False)

        if normalized_method == "GET" and normalized_path == "/events/recent":
            limit = max(int(query.get("limit", ["50"])[0]), 1)
            chat = str(query.get("chat", [""])[0])
            events = self._fetch_recent_events(limit=limit, chat=chat)
            return HTTPStatus.OK, {"events": events}

        if normalized_method == "GET" and normalized_path == "/history/senders":
            chat = str(query.get("chat", [""])[0]).strip()
            search_query = str(query.get("query", [""])[0]).strip()
            limit = min(max(int(query.get("limit", ["20"])[0]), 1), 100)
            if not chat:
                return HTTPStatus.BAD_REQUEST, {
                    "ok": False,
                    "error": "chat query parameter is required",
                }

            runtime = load_runtime_config(self._runtime_config_path)
            source_root = _resolve_wechat_decrypt_root(runtime)
            if source_root is None:
                return HTTPStatus.SERVICE_UNAVAILABLE, {
                    "ok": False,
                    "error": "wechat_decrypt_root_not_configured",
                }

            candidates = self._history_sender_searcher(source_root, chat, search_query, limit)
            return HTTPStatus.OK, {
                "candidates": [
                    payload
                    for payload in (_history_sender_to_payload(candidate) for candidate in candidates)
                    if payload["sender"]
                ]
            }

        if normalized_method == "GET" and normalized_path == "/logs/recent":
            limit = max(int(query.get("limit", ["120"])[0]), 1)
            return HTTPStatus.OK, {"logs": self._fetch_recent_logs(limit=limit)}

        if normalized_method == "POST" and normalized_path == "/mode":
            body = payload if isinstance(payload, dict) else {}
            mode = str(body.get("mode", "")).strip().lower()
            if mode not in {"normal", "rapid"}:
                return HTTPStatus.BAD_REQUEST, {
                    "ok": False,
                    "error": "mode must be normal or rapid",
                }

            state = self._store.load()
            state["mode"] = mode
            self._store.save(state)
            self._apply_runtime_mode_profile(mode)
            if self._process_manager.is_running():
                self._process_manager.restart(self._runtime_config_path, self._rules_path)
            return HTTPStatus.OK, self._build_status(limit=20, refresh_events=False)

        return HTTPStatus.NOT_FOUND, {"ok": False, "error": "route not found"}

    def _build_status(self, limit: int, refresh_events: bool = True) -> dict[str, Any]:
        state = self._store.load()
        arm_state = self._arm_state_payload()
        rules = self._read_rules()
        if refresh_events:
            events = self._fetch_recent_events(limit=limit, chat="")
        else:
            events = _cached_recent_events(state)
        recent_chats = _collect_recent_chats(events)
        first_rule = _first_enabled_rule(rules)

        status = {
            "service_state": "running" if self._process_manager.is_running() else "stopped",
            "watcher_state": "unavailable" if self._last_watcher_error else "running",
            "watcher_error": self._last_watcher_error,
            "armed": arm_state["armed"],
            "mode": state.get("mode", "normal"),
            "rule_pattern": str(first_rule.get("pattern", "")),
            "rules": rules,
            "active_target": state.get("active_target", {"talker": "", "display_name": "", "is_group": False}),
            "recent_events": events,
            "recent_chats": recent_chats,
            "replies": list(first_rule.get("replies", [])),
            "cooldown_ms": int(first_rule.get("cooldown_ms", 0)),
            "reply_delay_ms": int(first_rule.get("reply_delay_ms", 0)),
            "match_mode": str(first_rule.get("match_mode", "regex")),
            "rule_sender": str(first_rule.get("sender", "")),
            "rule_sender_name": str(first_rule.get("sender_name", "")),
            "max_triggers": arm_state["max_triggers"],
            "remaining_triggers": arm_state["remaining_triggers"],
            "recent_logs": self._fetch_recent_logs(limit=80),
        }
        self._store.save(status)
        return status

    def _read_rules(self) -> list[dict[str, Any]]:
        try:
            payload = json.loads(self._rules_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return [item for item in payload if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError):
            pass
        return []

    def _arm_state_payload(self) -> dict[str, Any]:
        arm = ArmStateStore(self._arm_state_path).read().to_dict()
        return {
            "armed": bool(arm["enabled"]),
            "max_triggers": int(arm["max_triggers"]),
            "remaining_triggers": arm["remaining_triggers"],
            "triggers_sent": int(arm["triggers_sent"]),
            "reason": str(arm["reason"]),
        }

    def _sync_desktop_rule_target(self, talker: str, is_group: bool) -> None:
        rules = self._read_rules()
        updated = False
        for rule in rules:
            if str(rule.get("id", "")).strip() != "desktop_rule":
                continue
            rule["talker"] = talker
            rule["chat_scope"] = "group" if is_group else "private"
            updated = True

        if not updated:
            return

        self._rules_path.write_text(
            json.dumps(rules, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _apply_runtime_mode_profile(self, mode: str) -> None:
        profile = RUNTIME_MODE_PROFILES.get(mode, RUNTIME_MODE_PROFILES["normal"])
        try:
            payload = json.loads(self._runtime_config_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                payload = {}
        except (OSError, json.JSONDecodeError):
            payload = {}

        payload.update(profile)
        self._runtime_config_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _fetch_recent_events(self, limit: int, chat: str) -> list[dict[str, object]]:
        try:
            runtime = load_runtime_config(self._runtime_config_path)
            watcher = self._watcher_factory(runtime)
            if not hasattr(watcher, "fetch_recent_events"):
                self._last_watcher_error = "watcher_fetch_not_supported"
                return []
            events = watcher.fetch_recent_events(limit=limit, chat=chat)
            if not isinstance(events, list):
                self._last_watcher_error = "watcher_payload_invalid"
                return []
            payloads = [_event_to_payload(event) for event in events if isinstance(event, MessageEvent)]
            self._last_watcher_error = ""
            return payloads
        except Exception as exc:
            self._last_watcher_error = str(exc) or exc.__class__.__name__
            state = self._store.load()
            fallback = state.get("recent_events", [])
            if isinstance(fallback, list):
                return [item for item in fallback if isinstance(item, dict)]
            return []

    def _fetch_recent_logs(self, limit: int) -> list[dict[str, str]]:
        logs_dir = self._runtime_root / "logs"
        candidates = [
            logs_dir / "wechat_automation.log",
            logs_dir / "live_bot" / "stdout.log",
            logs_dir / "live_bot" / "stderr.log",
            logs_dir / "wechat_decrypt" / "stdout.log",
            logs_dir / "wechat_decrypt" / "stderr.log",
        ]

        entries: list[dict[str, str]] = []
        for path in candidates:
            entries.extend(_read_log_file_tail(path, limit=limit))
        return entries[-limit:]

    def _ensure_source_available(self, runtime: RuntimeConfig) -> bool:
        source_root = _resolve_wechat_decrypt_root(runtime)
        if source_root is None:
            return True

        if self._source_health_check(runtime):
            return True

        self._source_process_manager.start(source_root)
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if self._source_health_check(runtime):
                self._last_watcher_error = ""
                return True
            time.sleep(0.25)

        self._last_watcher_error = "wechat_decrypt_not_ready"
        return False


def _read_log_file_tail(path: Path, limit: int) -> list[dict[str, str]]:
    if not path.exists() or not path.is_file():
        return []

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []

    source = path.name
    if path.parent.name == "live_bot":
        source = f"live_bot/{path.name}"
    if path.parent.name == "wechat_decrypt":
        source = f"wechat_decrypt/{path.name}"
    return [
        _log_to_payload(source, line.strip())
        for line in lines[-limit:]
        if line.strip()
    ]


def _collect_recent_chats(events: list[dict[str, object]]) -> list[dict[str, object]]:
    unique: list[dict[str, object]] = []
    seen: set[str] = set()
    for event in events:
        talker = str(event.get("talker", "")).strip()
        label = str(event.get("talker_name", "") or event.get("chat_name", "") or talker).strip()
        if not talker or talker in seen:
            continue
        seen.add(talker)
        unique.append(
            {
                "label": label or talker,
                "talker": talker,
                "is_group": bool(event.get("is_chat_room", False)),
            }
        )
    return unique


def _cached_recent_events(state: dict[str, Any]) -> list[dict[str, object]]:
    cached = state.get("recent_events", [])
    if not isinstance(cached, list):
        return []
    return [item for item in cached if isinstance(item, dict)]


def _first_enabled_rule(rules: list[dict[str, Any]]) -> dict[str, Any]:
    for rule in rules:
        if bool(rule.get("enabled", True)):
            return rule
    return {}


def _resolve_wechat_decrypt_root(runtime: RuntimeConfig) -> Path | None:
    candidates = [
        runtime.wechat_decrypt_root,
        os.environ.get("SUPER_IVAN_WECHAT_DECRYPT_ROOT", ""),
    ]
    for candidate in candidates:
        normalized = str(candidate or "").strip()
        if not normalized:
            continue
        path = Path(normalized)
        if (path / "main.py").exists():
            return path
    return None


def _default_source_health_check(runtime: RuntimeConfig) -> bool:
    url = f"{runtime.watcher_url.rstrip('/')}/api/history?limit=1"
    try:
        with urllib.request.urlopen(url, timeout=2):
            return True
    except Exception:
        return False


def create_app(
    runtime_root: Path | None = None,
    repo_root: Path | None = None,
    watcher_factory: Callable[[RuntimeConfig], object] = WechatDecryptHistoryWatcher,
    popen_factory: Callable[..., Any] = subprocess.Popen,
    python_executable: str = sys.executable,
    source_health_check: Callable[[RuntimeConfig], bool] | None = None,
    history_sender_searcher: Callable[[Path, str, str, int], list[object]] = search_history_senders,
) -> DesktopServiceApp:
    resolved_runtime_root = resolve_runtime_root(override=runtime_root)
    resolved_repo_root = resolve_repo_root(override=repo_root)
    return DesktopServiceApp(
        runtime_root=resolved_runtime_root,
        repo_root=resolved_repo_root,
        watcher_factory=watcher_factory,
        popen_factory=popen_factory,
        python_executable=python_executable,
        source_health_check=source_health_check,
        history_sender_searcher=history_sender_searcher,
    )


def create_http_server(
    app: DesktopServiceApp,
    host: str = "127.0.0.1",
    port: int = 18090,
) -> ThreadingHTTPServer:
    class JsonHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self._dispatch("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._dispatch("POST")

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _dispatch(self, method: str) -> None:
            payload: dict[str, Any] | None = None
            if method == "POST":
                content_length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(content_length) if content_length > 0 else b"{}"
                try:
                    payload = json.loads(body.decode("utf-8"))
                except json.JSONDecodeError:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {"ok": False, "error": "invalid json payload"},
                    )
                    return

            status, response_payload = app.handle_json(method, self.path, payload)
            self._write_json(status, response_payload)

        def _write_json(self, status: int, payload: dict[str, Any]) -> None:
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return ThreadingHTTPServer((host, port), JsonHandler)
