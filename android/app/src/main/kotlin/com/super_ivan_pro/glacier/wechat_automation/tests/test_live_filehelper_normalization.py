from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.matcher import match_rule
from core.models import RuntimeConfig, Rule
from core.watcher_adapter import WechatDecryptHistoryWatcher


class LiveFilehelperNormalizationTest(unittest.TestCase):
    def test_filehelper_payload_matches_chinese_talker_rule(self) -> None:
        watcher = WechatDecryptHistoryWatcher(RuntimeConfig())
        payload = {
            "timestamp": 1776787441,
            "chat": "filehelper",
            "username": "filehelper",
            "is_group": False,
            "sender": "",
            "type": "文本",
            "content": "START",
        }

        event = watcher._normalize_payload(payload)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.talker, "filehelper")
        self.assertEqual(event.display_talker, "文件传输助手")

        rule = Rule.from_dict(
            {
                "id": "filehelper_start_sequence",
                "enabled": True,
                "talker": "文件传输助手",
                "sender": "",
                "type": "text",
                "match_mode": "exact",
                "pattern": "START",
                "cooldown_ms": 800,
                "replies": ["TEST", "第二条"],
            }
        )

        result = match_rule(event, rule)
        self.assertTrue(result.matched)

    def test_group_payload_uses_stable_chatroom_talker_and_display_name(self) -> None:
        watcher = WechatDecryptHistoryWatcher(RuntimeConfig())
        payload = {
            "timestamp": 1779249772,
            "chat": "测试群聊",
            "username": "47561933285@chatroom",
            "is_group": True,
            "sender": "威士忌Wow",
            "type": "表情",
            "content": "嗯3",
        }

        event = watcher._normalize_payload(payload)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.talker, "47561933285@chatroom")
        self.assertEqual(event.display_talker, "测试群聊")

        rule = Rule.from_dict(
            {
                "id": "desktop_rule",
                "enabled": True,
                "talker": "47561933285@chatroom",
                "sender": "",
                "chat_scope": "group",
                "type": "text",
                "match_mode": "regex",
                "pattern": "嗯3",
                "cooldown_ms": 0,
                "replies": ["Slytherin"],
            }
        )

        result = match_rule(event, rule)
        self.assertTrue(result.matched)


if __name__ == "__main__":
    unittest.main()
