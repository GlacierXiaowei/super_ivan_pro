from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.models import MessageEvent, MessageType, RuntimeConfig
from core.watcher_adapter import WechatDecryptHistoryWatcher
from scripts.web_console import create_app


class WebConsoleWatcherSnapshotTest(unittest.TestCase):
    def test_snapshot_normalizes_recent_payloads(self) -> None:
        watcher = WechatDecryptHistoryWatcher(RuntimeConfig())
        payloads = [
            {
                "timestamp": 1776787441,
                "chat": "filehelper",
                "username": "filehelper",
                "is_group": False,
                "sender": "",
                "type": "文本",
                "content": "START",
            }
        ]

        events = watcher.normalize_payloads(payloads)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].display_talker, "文件传输助手")


class DummyWatcher:
    def __init__(self, runtime: RuntimeConfig) -> None:
        self.runtime = runtime

    def fetch_recent_events(self, limit: int = 50, chat: str = "") -> list[MessageEvent]:
        return [
            MessageEvent(
                seq="1",
                timestamp="1",
                talker="filehelper",
                talker_name="文件传输助手",
                is_chat_room=False,
                sender="",
                sender_name="",
                message_type=MessageType.TEXT,
                content="START",
            )
        ]


class WebConsoleApiTest(unittest.TestCase):
    def test_rules_round_trip_and_recent_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_path = Path(tmp) / "runtime.json"
            rules_path = Path(tmp) / "rules.json"
            runtime_path.write_text(
                json.dumps(
                    {
                        "watcher_url": "http://127.0.0.1:5678",
                        "sender_backend": "dry_run",
                        "dry_run": True,
                    }
                ),
                encoding="utf-8",
            )
            rules_path.write_text("[]", encoding="utf-8")

            app = create_app(
                runtime_path=runtime_path,
                rules_path=rules_path,
                watcher_factory=DummyWatcher,
            )
            client = app.test_client()

            get_rules_response = client.get("/api/rules")
            self.assertEqual(get_rules_response.status_code, 200)
            self.assertEqual(get_rules_response.get_json(), [])

            save_payload = [
                {
                    "id": "filehelper_start_sequence",
                    "enabled": True,
                    "talker": "文件传输助手",
                    "sender": "",
                    "chat_scope": "private",
                    "type": "text",
                    "match_mode": "exact",
                    "pattern": "START",
                    "cooldown_ms": 800,
                    "replies": ["TEST", "第二条"],
                }
            ]
            save_response = client.post("/api/rules", json=save_payload)
            self.assertEqual(save_response.status_code, 200)

            persisted = json.loads(rules_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted, save_payload)

            get_events_response = client.get("/api/events?limit=10")
            self.assertEqual(get_events_response.status_code, 200)
            events = get_events_response.get_json()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["talker_name"], "文件传输助手")
            self.assertEqual(events[0]["chat_scope"], "private")


if __name__ == "__main__":
    unittest.main()
