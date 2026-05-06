from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.matcher import match_rule
from core.models import MessageEvent, MessageType, Rule


class MatcherChatScopeTest(unittest.TestCase):
    def test_private_scope_accepts_private_event(self) -> None:
        rule = Rule.from_dict(
            {
                "id": "private_only",
                "enabled": True,
                "talker": "文件传输助手",
                "sender": "",
                "type": "text",
                "chat_scope": "private",
                "match_mode": "exact",
                "pattern": "START",
                "cooldown_ms": 0,
                "replies": ["OK"],
            }
        )
        message = MessageEvent(
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

        result = match_rule(message, rule)
        self.assertTrue(result.matched)

    def test_private_scope_rejects_group_event(self) -> None:
        rule = Rule.from_dict(
            {
                "id": "private_only",
                "enabled": True,
                "talker": "测试群",
                "sender": "",
                "type": "text",
                "chat_scope": "private",
                "match_mode": "exact",
                "pattern": "START",
                "cooldown_ms": 0,
                "replies": ["OK"],
            }
        )
        message = MessageEvent(
            seq="2",
            timestamp="2",
            talker="123@chatroom",
            talker_name="测试群",
            is_chat_room=True,
            sender="Alice",
            sender_name="Alice",
            message_type=MessageType.TEXT,
            content="START",
        )

        result = match_rule(message, rule)
        self.assertFalse(result.matched)
        self.assertEqual(result.reason, "chat_scope_mismatch")

    def test_any_match_mode_accepts_any_content_after_scope_and_type_match(self) -> None:
        rule = Rule.from_dict(
            {
                "id": "any_message",
                "enabled": True,
                "talker": "测试群",
                "sender": "",
                "type": "unknown",
                "chat_scope": "group",
                "match_mode": "any",
                "pattern": "",
                "cooldown_ms": 0,
                "replies": ["OK"],
            }
        )
        message = MessageEvent(
            seq="3",
            timestamp="3",
            talker="123@chatroom",
            talker_name="测试群",
            is_chat_room=True,
            sender="Alice",
            sender_name="Alice",
            message_type=MessageType.EMOJI,
            content="",
        )

        result = match_rule(message, rule)
        self.assertTrue(result.matched)
        self.assertEqual(result.reason, "matched")

    def test_any_match_mode_still_rejects_wrong_talker(self) -> None:
        rule = Rule.from_dict(
            {
                "id": "any_message",
                "enabled": True,
                "talker": "目标群",
                "sender": "",
                "type": "unknown",
                "chat_scope": "group",
                "match_mode": "any",
                "pattern": "",
                "cooldown_ms": 0,
                "replies": ["OK"],
            }
        )
        message = MessageEvent(
            seq="4",
            timestamp="4",
            talker="123@chatroom",
            talker_name="其他群",
            is_chat_room=True,
            sender="Alice",
            sender_name="Alice",
            message_type=MessageType.IMAGE,
            content="",
        )

        result = match_rule(message, rule)
        self.assertFalse(result.matched)
        self.assertEqual(result.reason, "talker_mismatch")


if __name__ == "__main__":
    unittest.main()
