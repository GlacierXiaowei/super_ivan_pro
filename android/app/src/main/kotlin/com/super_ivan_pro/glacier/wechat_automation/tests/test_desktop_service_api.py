from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(ROOT))

from core.models import MessageEvent, MessageType, RuntimeConfig  # noqa: E402
from desktop_service.http_api import create_app  # noqa: E402


class DummyWatcher:
    def __init__(self, runtime: RuntimeConfig) -> None:
        self.runtime = runtime

    def fetch_recent_events(self, limit: int = 50, chat: str = "") -> list[MessageEvent]:
        return [
            MessageEvent(
                seq="1",
                timestamp="1711000001",
                talker="filehelper",
                talker_name="文件传输助手",
                is_chat_room=False,
                sender="",
                sender_name="",
                message_type=MessageType.TEXT,
                content="START",
            ),
            MessageEvent(
                seq="2",
                timestamp="1711000002",
                talker="group-1",
                talker_name="测试群",
                is_chat_room=True,
                sender="alice",
                sender_name="Alice",
                message_type=MessageType.TEXT,
                content="ping",
            ),
        ][: max(limit, 1)]


class FakeProcess:
    def __init__(self) -> None:
        self.returncode = None
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = 0

    def wait(self, timeout: float | None = None) -> int:
        _ = timeout
        if self.returncode is None:
            self.returncode = 0
        return self.returncode

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9


class FakePopenFactory:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.process = FakeProcess()

    def __call__(self, args: list[str], **kwargs: object) -> FakeProcess:
        self.calls.append({"args": list(args), "kwargs": dict(kwargs)})
        return self.process


class DesktopServiceApiTest(unittest.TestCase):
    def _build_repo_fixture(self, root: Path) -> None:
        (root / "config").mkdir(parents=True, exist_ok=True)
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        (root / "scripts" / "run_bot.py").write_text(
            "print('bot placeholder')\n",
            encoding="utf-8",
        )
        (root / "config" / "runtime.local.json").write_text(
            json.dumps(
                {
                    "watcher_url": "http://127.0.0.1:5678",
                    "sender_backend": "dry_run",
                    "dry_run": True,
                }
            ),
            encoding="utf-8",
        )
        (root / "config" / "rules.local.json").write_text(
            json.dumps(
                [
                    {
                        "id": "demo",
                        "enabled": True,
                        "talker": "filehelper",
                        "sender": "",
                        "chat_scope": "private",
                        "type": "text",
                        "match_mode": "exact",
                        "pattern": "START",
                        "cooldown_ms": 800,
                        "replies": ["ACK"],
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (root / "config" / "arm_state.local.json").write_text(
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
            ),
            encoding="utf-8",
        )

    def test_status_and_service_lifecycle_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            runtime_root = tmp_path / "desktop-runtime"
            self._build_repo_fixture(repo_root)
            popen_factory = FakePopenFactory()
            app = create_app(
                runtime_root=runtime_root,
                repo_root=repo_root,
                watcher_factory=DummyWatcher,
                popen_factory=popen_factory,
            )

            status_code, status = app.handle_json("GET", "/status")
            self.assertEqual(status_code, 200)
            self.assertEqual(status["mode"], "normal")
            self.assertEqual(status["service_state"], "stopped")
            self.assertEqual(status["rule_pattern"], "START")
            self.assertIn("recent_chats", status)
            self.assertEqual(status["max_triggers"], 1)
            self.assertEqual(status["remaining_triggers"], 1)
            self.assertEqual(status["recent_chats"][0], "文件传输助手")

            status_code, updated = app.handle_json(
                "POST",
                "/targets/active",
                {
                    "talker": "filehelper",
                    "display_name": "文件传输助手",
                    "is_group": False,
                },
            )
            self.assertEqual(status_code, 200)
            self.assertEqual(updated["active_target"]["display_name"], "文件传输助手")

            status_code, rapid = app.handle_json("POST", "/mode", {"mode": "rapid"})
            self.assertEqual(status_code, 200)
            self.assertEqual(rapid["mode"], "rapid")

            status_code, armed = app.handle_json("POST", "/arm-state", {"enabled": True, "max_triggers": 3})
            self.assertEqual(status_code, 200)
            self.assertTrue(armed["armed"])
            self.assertEqual(armed["max_triggers"], 3)

            status_code, running = app.handle_json("POST", "/services/start")
            self.assertEqual(status_code, 200)
            self.assertEqual(running["service_state"], "running")
            self.assertEqual(len(popen_factory.calls), 1)
            popen_args = popen_factory.calls[0]["args"]
            self.assertIn("--live", popen_args)
            self.assertIn(str(runtime_root / "config" / "runtime.local.json"), popen_args)
            self.assertIn(str(runtime_root / "config" / "rules.local.json"), popen_args)

            status_code, latest = app.handle_json("GET", "/status")
            self.assertEqual(status_code, 200)
            self.assertEqual(latest["active_target"]["talker"], "filehelper")
            self.assertEqual(latest["mode"], "rapid")
            self.assertTrue(latest["armed"])
            self.assertEqual(latest["remaining_triggers"], 3)
            self.assertEqual(latest["service_state"], "running")

            status_code, stopped = app.handle_json("POST", "/services/stop")
            self.assertEqual(status_code, 200)
            self.assertEqual(stopped["service_state"], "stopped")
            self.assertTrue(popen_factory.process.terminated)

    def test_rules_arm_state_and_recent_events_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            runtime_root = tmp_path / "desktop-runtime"
            self._build_repo_fixture(repo_root)
            app = create_app(
                runtime_root=runtime_root,
                repo_root=repo_root,
                watcher_factory=DummyWatcher,
                popen_factory=FakePopenFactory(),
            )

            status_code, rules = app.handle_json("GET", "/rules")
            self.assertEqual(status_code, 200)
            self.assertEqual(len(rules["rules"]), 1)

            payload = [
                {
                    "id": "r2",
                    "enabled": True,
                    "talker": "filehelper",
                    "sender": "",
                    "chat_scope": "private",
                    "type": "text",
                    "match_mode": "exact",
                    "pattern": "PING",
                    "cooldown_ms": 200,
                    "replies": ["PONG"],
                }
            ]
            status_code, updated_rules = app.handle_json("POST", "/rules", {"rules": payload})
            self.assertEqual(status_code, 200)
            self.assertEqual(updated_rules["rules"][0]["pattern"], "PING")

            status_code, status = app.handle_json("GET", "/status")
            self.assertEqual(status_code, 200)
            self.assertEqual(status["rule_pattern"], "PING")
            self.assertEqual(status["replies"], ["PONG"])
            self.assertEqual(status["cooldown_ms"], 200)
            self.assertEqual(status["match_mode"], "exact")

            status_code, arm_state = app.handle_json("GET", "/arm-state")
            self.assertEqual(status_code, 200)
            self.assertFalse(arm_state["armed"])

            status_code, events_payload = app.handle_json("GET", "/events/recent")
            self.assertEqual(status_code, 200)
            self.assertEqual(len(events_payload["events"]), 2)
            self.assertEqual(events_payload["events"][0]["talker_name"], "文件传输助手")

    def test_rejects_incomplete_target_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            runtime_root = tmp_path / "desktop-runtime"
            self._build_repo_fixture(repo_root)
            app = create_app(
                runtime_root=runtime_root,
                repo_root=repo_root,
                watcher_factory=DummyWatcher,
                popen_factory=FakePopenFactory(),
            )
            status_code, payload = app.handle_json("POST", "/targets/active", {"talker": "a"})
            self.assertEqual(status_code, 400)
            self.assertEqual(payload["ok"], False)


if __name__ == "__main__":
    unittest.main()
