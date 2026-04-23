from __future__ import annotations

import json
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

from core.arm_state import ArmStateStore
from core.config_loader import load_runtime_config
from core.models import MessageEvent, RuntimeConfig
from core.watcher_adapter import WechatDecryptHistoryWatcher

from .config_paths import ensure_runtime_files, resolve_repo_root, resolve_runtime_root
from .state_store import DesktopStateStore


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
    ) -> None:
        self._runtime_root = Path(runtime_root)
        self._repo_root = Path(repo_root)
        self._paths = ensure_runtime_files(self._runtime_root, self._repo_root)
        self._runtime_config_path = self._paths["runtime"]
        self._rules_path = self._paths["rules"]
        self._arm_state_path = self._paths["arm_state"]
        self._store = DesktopStateStore(self._runtime_root)
        self._watcher_factory = watcher_factory
        self._process_manager = BotProcessManager(
            repo_root=self._repo_root,
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
            self._process_manager.start(self._runtime_config_path, self._rules_path)
            return HTTPStatus.OK, self._build_status(limit=20)

        if normalized_method == "POST" and normalized_path == "/services/stop":
            self._process_manager.stop()
            return HTTPStatus.OK, self._build_status(limit=20)

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
            return HTTPStatus.OK, self._build_status(limit=20)

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
            return HTTPStatus.OK, {"rules": rules}

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
            return HTTPStatus.OK, self._build_status(limit=20)

        if normalized_method == "GET" and normalized_path == "/events/recent":
            limit = max(int(query.get("limit", ["50"])[0]), 1)
            chat = str(query.get("chat", [""])[0])
            events = self._fetch_recent_events(limit=limit, chat=chat)
            return HTTPStatus.OK, {"events": events}

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
            return HTTPStatus.OK, self._build_status(limit=20)

        return HTTPStatus.NOT_FOUND, {"ok": False, "error": "route not found"}

    def _build_status(self, limit: int) -> dict[str, Any]:
        state = self._store.load()
        arm_state = self._arm_state_payload()
        rules = self._read_rules()
        events = self._fetch_recent_events(limit=limit, chat="")
        recent_chats = _collect_recent_chats(events)
        first_rule = _first_enabled_rule(rules)

        status = {
            "service_state": "running" if self._process_manager.is_running() else "stopped",
            "armed": arm_state["armed"],
            "mode": state.get("mode", "normal"),
            "rule_pattern": str(first_rule.get("pattern", "")),
            "active_target": state.get("active_target", {"talker": "", "display_name": "", "is_group": False}),
            "recent_events": events,
            "recent_chats": recent_chats,
            "replies": list(first_rule.get("replies", [])),
            "cooldown_ms": int(first_rule.get("cooldown_ms", 0)),
            "match_mode": str(first_rule.get("match_mode", "regex")),
            "max_triggers": arm_state["max_triggers"],
            "remaining_triggers": arm_state["remaining_triggers"],
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

    def _fetch_recent_events(self, limit: int, chat: str) -> list[dict[str, object]]:
        try:
            runtime = load_runtime_config(self._runtime_config_path)
            watcher = self._watcher_factory(runtime)
            if not hasattr(watcher, "fetch_recent_events"):
                return []
            events = watcher.fetch_recent_events(limit=limit, chat=chat)
            if not isinstance(events, list):
                return []
            payloads = [_event_to_payload(event) for event in events if isinstance(event, MessageEvent)]
            return payloads
        except Exception:
            state = self._store.load()
            fallback = state.get("recent_events", [])
            if isinstance(fallback, list):
                return [item for item in fallback if isinstance(item, dict)]
            return []


def _collect_recent_chats(events: list[dict[str, object]]) -> list[str]:
    unique: list[str] = []
    for event in events:
        talker_name = str(event.get("talker_name", "")).strip()
        if talker_name and talker_name not in unique:
            unique.append(talker_name)
    return unique


def _first_enabled_rule(rules: list[dict[str, Any]]) -> dict[str, Any]:
    for rule in rules:
        if bool(rule.get("enabled", True)):
            return rule
    return {}


def create_app(
    runtime_root: Path | None = None,
    repo_root: Path | None = None,
    watcher_factory: Callable[[RuntimeConfig], object] = WechatDecryptHistoryWatcher,
    popen_factory: Callable[..., Any] = subprocess.Popen,
    python_executable: str = sys.executable,
) -> DesktopServiceApp:
    resolved_runtime_root = resolve_runtime_root(override=runtime_root)
    resolved_repo_root = resolve_repo_root(override=repo_root)
    return DesktopServiceApp(
        runtime_root=resolved_runtime_root,
        repo_root=resolved_repo_root,
        watcher_factory=watcher_factory,
        popen_factory=popen_factory,
        python_executable=python_executable,
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
