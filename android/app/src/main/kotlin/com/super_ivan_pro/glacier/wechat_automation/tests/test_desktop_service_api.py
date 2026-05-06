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


class FailingWatcher:
    def __init__(self, runtime: RuntimeConfig) -> None:
        self.runtime = runtime

    def fetch_recent_events(self, limit: int = 50, chat: str = "") -> list[MessageEvent]:
        _ = limit
        _ = chat
        raise ConnectionRefusedError("watcher offline")


class CountingWatcher:
    calls = 0

    def __init__(self, runtime: RuntimeConfig) -> None:
        self.runtime = runtime

    def fetch_recent_events(self, limit: int = 50, chat: str = "") -> list[MessageEvent]:
        _ = limit
        _ = chat
        type(self).calls += 1
        return []


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
        self.processes: list[FakeProcess] = []

    def __call__(self, args: list[str], **kwargs: object) -> FakeProcess:
        process = FakeProcess()
        self.calls.append({"args": list(args), "kwargs": dict(kwargs)})
        self.processes.append(process)
        return process


class SequenceSourceHealthCheck:
    def __init__(self, results: list[bool]) -> None:
        self.results = list(results)
        self.calls = 0

    def __call__(self, runtime: RuntimeConfig) -> bool:
        _ = runtime
        self.calls += 1
        if self.results:
            return self.results.pop(0)
        return False


def fake_history_sender_searcher(source_root: Path, chat: str, query: str, limit: int) -> list[dict[str, object]]:
    return [
        {
            "sender": f"wxid_{query.lower()}",
            "sender_name": "Alice Remark",
            "last_timestamp": 1778000003,
            "last_content": f"{chat} recent message",
            "message_count": min(limit, 2),
        }
    ]


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
            self.assertEqual(status["recent_chats"][0]["label"], "文件传输助手")
            self.assertEqual(status["recent_chats"][0]["talker"], "filehelper")
            self.assertFalse(status["recent_chats"][0]["is_group"])

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
            self.assertTrue(popen_factory.processes[0].terminated)

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

    def test_history_senders_endpoint_returns_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            runtime_root = tmp_path / "desktop-runtime"
            source_root = tmp_path / "wechat-decrypt"
            source_root.mkdir(parents=True)
            (source_root / "main.py").write_text("print('source placeholder')\n", encoding="utf-8")
            self._build_repo_fixture(repo_root)
            runtime_path = repo_root / "config" / "runtime.local.json"
            runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
            runtime_payload["wechat_decrypt_root"] = str(source_root)
            runtime_path.write_text(json.dumps(runtime_payload), encoding="utf-8")
            app = create_app(
                runtime_root=runtime_root,
                repo_root=repo_root,
                watcher_factory=DummyWatcher,
                popen_factory=FakePopenFactory(),
                history_sender_searcher=fake_history_sender_searcher,
            )

            status_code, payload = app.handle_json(
                "GET",
                "/history/senders?chat=123456%40chatroom&query=Alice&limit=5",
            )

            self.assertEqual(status_code, 200)
            self.assertEqual(payload["candidates"][0]["sender"], "wxid_alice")
            self.assertEqual(payload["candidates"][0]["sender_name"], "Alice Remark")
            self.assertEqual(payload["candidates"][0]["message_count"], 2)

    def test_post_responses_return_cached_status_without_refreshing_watcher(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            runtime_root = tmp_path / "desktop-runtime"
            self._build_repo_fixture(repo_root)
            CountingWatcher.calls = 0
            app = create_app(
                runtime_root=runtime_root,
                repo_root=repo_root,
                watcher_factory=CountingWatcher,
                popen_factory=FakePopenFactory(),
            )

            status_code, initial = app.handle_json("GET", "/status")
            self.assertEqual(status_code, 200)
            self.assertEqual(CountingWatcher.calls, 1)
            self.assertEqual(initial["recent_events"], [])

            status_code, updated = app.handle_json("POST", "/mode", {"mode": "rapid"})
            self.assertEqual(status_code, 200)
            self.assertEqual(updated["mode"], "rapid")
            self.assertIn("service_state", updated)
            self.assertIn("recent_events", updated)
            self.assertEqual(CountingWatcher.calls, 1)

    def test_recent_logs_endpoint_and_status_include_log_lines(self) -> None:
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

            logs_dir = runtime_root / "logs"
            (logs_dir / "wechat_automation.log").write_text(
                "2026-05-06 INFO old line\n"
                "2026-05-06 INFO rule_match rule=desktop_rule seq=1\n",
                encoding="utf-8",
            )
            live_bot_dir = logs_dir / "live_bot"
            live_bot_dir.mkdir(parents=True, exist_ok=True)
            (live_bot_dir / "stderr.log").write_text(
                "2026-05-06 ERROR chat_input_not_focused\n",
                encoding="utf-8",
            )

            status_code, logs_payload = app.handle_json("GET", "/logs/recent?limit=2")
            self.assertEqual(status_code, 200)
            self.assertEqual(
                [item["message"] for item in logs_payload["logs"]],
                [
                    "2026-05-06 INFO rule_match rule=desktop_rule seq=1",
                    "2026-05-06 ERROR chat_input_not_focused",
                ],
            )
            self.assertEqual(logs_payload["logs"][0]["source"], "wechat_automation.log")

            status_code, status = app.handle_json("GET", "/status")
            self.assertEqual(status_code, 200)
            self.assertIn("recent_logs", status)
            self.assertGreaterEqual(len(status["recent_logs"]), 2)

    def test_status_reports_watcher_unavailable_when_history_fetch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            runtime_root = tmp_path / "desktop-runtime"
            self._build_repo_fixture(repo_root)
            app = create_app(
                runtime_root=runtime_root,
                repo_root=repo_root,
                watcher_factory=FailingWatcher,
                popen_factory=FakePopenFactory(),
            )

            status_code, status = app.handle_json("GET", "/status")
            self.assertEqual(status_code, 200)
            self.assertEqual(status["watcher_state"], "unavailable")
            self.assertEqual(status["watcher_error"], "watcher offline")

    def test_rule_update_restarts_running_bot(self) -> None:
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

            status_code, running = app.handle_json("POST", "/services/start")
            self.assertEqual(status_code, 200)
            self.assertEqual(running["service_state"], "running")
            self.assertEqual(len(popen_factory.calls), 1)

            payload = [
                {
                    "id": "desktop_rule",
                    "enabled": True,
                    "talker": "wxid_target",
                    "sender": "",
                    "chat_scope": "private",
                    "type": "text",
                    "match_mode": "regex",
                    "pattern": "START",
                    "cooldown_ms": 300,
                    "replies": ["ACK"],
                }
            ]
            status_code, updated = app.handle_json("POST", "/rules", {"rules": payload})
            self.assertEqual(status_code, 200)
            self.assertEqual(updated["rules"][0]["talker"], "wxid_target")
            self.assertEqual(len(popen_factory.calls), 2)
            self.assertTrue(popen_factory.processes[0].terminated)
            app.handle_json("POST", "/services/stop")

    def test_start_launches_wechat_decrypt_source_before_bot_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            runtime_root = tmp_path / "desktop-runtime"
            source_root = tmp_path / "wechat-decrypt"
            source_root.mkdir(parents=True)
            (source_root / "main.py").write_text("print('source placeholder')\n", encoding="utf-8")
            self._build_repo_fixture(repo_root)
            runtime_path = repo_root / "config" / "runtime.local.json"
            runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
            runtime_payload["wechat_decrypt_root"] = str(source_root)
            runtime_path.write_text(json.dumps(runtime_payload), encoding="utf-8")
            popen_factory = FakePopenFactory()
            source_health = SequenceSourceHealthCheck([False, True])
            app = create_app(
                runtime_root=runtime_root,
                repo_root=repo_root,
                watcher_factory=DummyWatcher,
                popen_factory=popen_factory,
                source_health_check=source_health,
            )

            status_code, running = app.handle_json("POST", "/services/start")
            self.assertEqual(status_code, 200)
            self.assertEqual(running["service_state"], "running")
            self.assertEqual(running["watcher_state"], "running")
            self.assertEqual(len(popen_factory.calls), 2)
            self.assertEqual(popen_factory.calls[0]["args"][1], "main.py")
            self.assertEqual(popen_factory.calls[0]["kwargs"]["cwd"], str(source_root))
            self.assertIn("--live", popen_factory.calls[1]["args"])
            self.assertGreaterEqual(source_health.calls, 2)
            app.handle_json("POST", "/services/stop")

    def test_restart_endpoint_restarts_running_bot(self) -> None:
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

            app.handle_json("POST", "/services/start")
            self.assertEqual(len(popen_factory.calls), 1)

            status_code, restarted = app.handle_json("POST", "/services/restart")
            self.assertEqual(status_code, 200)
            self.assertEqual(restarted["service_state"], "running")
            self.assertEqual(len(popen_factory.calls), 2)
            self.assertTrue(popen_factory.processes[0].terminated)
            app.handle_json("POST", "/services/stop")

    def test_target_update_syncs_desktop_rule_and_restarts_running_bot(self) -> None:
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

            app.handle_json(
                "POST",
                "/rules",
                {
                    "rules": [
                        {
                            "id": "desktop_rule",
                            "enabled": True,
                            "talker": "old_talker",
                            "sender": "",
                            "chat_scope": "private",
                            "type": "text",
                            "match_mode": "regex",
                            "pattern": "START",
                            "cooldown_ms": 800,
                            "replies": ["ACK"],
                        }
                    ]
                },
            )
            app.handle_json("POST", "/services/start")
            self.assertEqual(len(popen_factory.calls), 1)

            status_code, updated = app.handle_json(
                "POST",
                "/targets/active",
                {
                    "talker": "57581313812@chatroom",
                    "display_name": "测试群",
                    "is_group": True,
                },
            )
            self.assertEqual(status_code, 200)
            self.assertEqual(updated["active_target"]["talker"], "57581313812@chatroom")
            self.assertEqual(len(popen_factory.calls), 2)
            self.assertTrue(popen_factory.processes[0].terminated)

            stored_rules = json.loads((runtime_root / "config" / "rules.local.json").read_text(encoding="utf-8"))
            self.assertEqual(stored_rules[0]["talker"], "57581313812@chatroom")
            self.assertEqual(stored_rules[0]["chat_scope"], "group")
            app.handle_json("POST", "/services/stop")

    def test_rapid_mode_updates_runtime_profile_and_restarts_running_bot(self) -> None:
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

            app.handle_json("POST", "/services/start")
            self.assertEqual(len(popen_factory.calls), 1)

            status_code, rapid = app.handle_json("POST", "/mode", {"mode": "rapid"})
            self.assertEqual(status_code, 200)
            self.assertEqual(rapid["mode"], "rapid")
            self.assertEqual(len(popen_factory.calls), 2)
            self.assertTrue(popen_factory.processes[0].terminated)

            runtime_payload = json.loads(
                (runtime_root / "config" / "runtime.local.json").read_text(encoding="utf-8")
            )
            self.assertEqual(runtime_payload["poll_interval_ms"], 20)
            self.assertEqual(runtime_payload["history_limit"], 50)
            self.assertEqual(runtime_payload["inter_message_delay_ms"], 0)
            self.assertEqual(runtime_payload["retry_count"], 0)
            self.assertTrue(runtime_payload["current_chat_fast_send"])

            status_code, normal = app.handle_json("POST", "/mode", {"mode": "normal"})
            self.assertEqual(status_code, 200)
            self.assertEqual(normal["mode"], "normal")
            self.assertEqual(len(popen_factory.calls), 3)
            self.assertTrue(popen_factory.processes[1].terminated)

            runtime_payload = json.loads(
                (runtime_root / "config" / "runtime.local.json").read_text(encoding="utf-8")
            )
            self.assertEqual(runtime_payload["poll_interval_ms"], 300)
            self.assertEqual(runtime_payload["history_limit"], 200)
            self.assertEqual(runtime_payload["inter_message_delay_ms"], 180)
            self.assertEqual(runtime_payload["retry_count"], 1)
            self.assertFalse(runtime_payload["current_chat_fast_send"])
            app.handle_json("POST", "/services/stop")

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
