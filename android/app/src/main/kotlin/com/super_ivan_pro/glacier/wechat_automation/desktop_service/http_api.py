from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .config_paths import resolve_runtime_root
from .state_store import DesktopStateStore


class DesktopServiceApp:
    def __init__(self, runtime_root: Path) -> None:
        self._store = DesktopStateStore(runtime_root)

    def handle_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        normalized_method = method.upper()
        normalized_path = urlparse(path).path
        state = self._store.load()

        if normalized_method == "GET" and normalized_path == "/status":
            state["service_state"] = "running"
            self._store.save(state)
            return HTTPStatus.OK, state

        if normalized_method == "POST" and normalized_path == "/targets/active":
            body = payload if isinstance(payload, dict) else {}
            required = ("talker", "display_name", "is_group")
            missing = [key for key in required if key not in body]
            if missing:
                return HTTPStatus.BAD_REQUEST, {
                    "ok": False,
                    "error": f"missing required fields: {', '.join(missing)}",
                }

            state["active_target"] = {
                "talker": str(body["talker"]),
                "display_name": str(body["display_name"]),
                "is_group": bool(body["is_group"]),
            }
            self._store.save(state)
            return HTTPStatus.OK, state

        if normalized_method == "POST" and normalized_path == "/mode":
            body = payload if isinstance(payload, dict) else {}
            mode = str(body.get("mode", "")).strip().lower()
            if mode not in {"normal", "rapid"}:
                return HTTPStatus.BAD_REQUEST, {
                    "ok": False,
                    "error": "mode must be normal or rapid",
                }

            state["mode"] = mode
            self._store.save(state)
            return HTTPStatus.OK, state

        return HTTPStatus.NOT_FOUND, {"ok": False, "error": "route not found"}


def create_app(runtime_root: Path | None = None) -> DesktopServiceApp:
    return DesktopServiceApp(resolve_runtime_root(override=runtime_root))


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
