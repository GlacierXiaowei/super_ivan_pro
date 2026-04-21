from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable

from flask import Flask, jsonify, request, send_from_directory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config_loader import load_runtime_config
from core.models import MessageEvent, RuntimeConfig
from core.watcher_adapter import WechatDecryptHistoryWatcher


WEB_DIR = ROOT / "web"


def _event_to_payload(event: MessageEvent) -> dict[str, object]:
    return {
        "seq": event.seq,
        "timestamp": event.timestamp,
        "talker": event.talker,
        "talker_name": event.display_talker,
        "sender": event.sender,
        "sender_name": event.display_sender,
        "is_chat_room": event.is_chat_room,
        "chat_scope": "group" if event.is_chat_room else "private",
        "type": event.message_type.value,
        "content": event.content,
        "raw": event.raw,
    }


def create_app(
    runtime_path: str | Path,
    rules_path: str | Path,
    watcher_factory: Callable[[RuntimeConfig], object] | None = None,
) -> Flask:
    app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="/web")
    resolved_runtime_path = Path(runtime_path).resolve()
    resolved_rules_path = Path(rules_path).resolve()

    @app.get("/")
    def index() -> object:
        return send_from_directory(WEB_DIR, "index.html")

    @app.get("/web/<path:filename>")
    def web_assets(filename: str) -> object:
        return send_from_directory(WEB_DIR, filename)

    @app.get("/api/rules")
    def get_rules() -> object:
        payload = json.loads(resolved_rules_path.read_text(encoding="utf-8"))
        return jsonify(payload)

    @app.post("/api/rules")
    def save_rules() -> object:
        payload = request.get_json(force=True)
        if not isinstance(payload, list):
            return jsonify({"ok": False, "error": "rules payload must be a list"}), 400
        resolved_rules_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return jsonify({"ok": True})

    @app.get("/api/events")
    def get_events() -> object:
        runtime = load_runtime_config(resolved_runtime_path)
        factory = watcher_factory or WechatDecryptHistoryWatcher
        watcher = factory(runtime)
        if not hasattr(watcher, "fetch_recent_events"):
            return jsonify({"ok": False, "error": "watcher does not support snapshots"}), 500

        limit = max(int(request.args.get("limit", "50")), 1)
        chat = str(request.args.get("chat", ""))
        events = watcher.fetch_recent_events(limit=limit, chat=chat)
        return jsonify([_event_to_payload(event) for event in events])

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the WeChat automation web console.")
    parser.add_argument("--runtime", required=True, help="Path to runtime config JSON/YAML.")
    parser.add_argument("--rules", required=True, help="Path to rules config JSON/YAML.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for the local console.")
    parser.add_argument("--port", type=int, default=8090, help="Port for the local console.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = create_app(runtime_path=args.runtime, rules_path=args.rules)
    app.run(host=args.host, port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
