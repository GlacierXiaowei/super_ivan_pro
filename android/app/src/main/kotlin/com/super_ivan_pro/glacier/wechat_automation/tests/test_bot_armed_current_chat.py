from __future__ import annotations

import logging
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.arm_state import ArmStateStore  # noqa: E402
from core.bot import WeChatAutomationBot  # noqa: E402
from core.dispatcher import SendDispatcher  # noqa: E402
from core.models import ChatScope, MatchMode, MessageEvent, MessageType, Rule, RuntimeConfig  # noqa: E402


class MemorySender:
    def __init__(self, calls: list[str] | None = None) -> None:
        self.sent: list[str] = []
        self.calls = calls

    def send_text(self, context: MessageEvent, message: str) -> None:
        if self.calls is not None:
            self.calls.append(f"send:{message}")
        self.sent.append(message)


def build_event(seq: str) -> MessageEvent:
    return MessageEvent(
        seq=seq,
        timestamp="1",
        talker="filehelper",
        talker_name="文件传输助手",
        is_chat_room=False,
        sender="",
        sender_name="",
        message_type=MessageType.TEXT,
        content="START",
    )


def build_group_event(seq: str, sender: str, content: str) -> MessageEvent:
    return MessageEvent(
        seq=seq,
        timestamp="1",
        talker="47561933285@chatroom",
        talker_name="47561933285@chatroom",
        is_chat_room=True,
        sender=sender,
        sender_name=sender,
        message_type=MessageType.TEXT,
        content=content,
    )


def build_rule(reply_delay_ms: int = 0) -> Rule:
    return Rule.from_dict(
        {
            "id": "filehelper_start_sequence",
            "enabled": True,
            "talker": "文件传输助手",
            "sender": "",
            "chat_scope": "private",
            "type": "text",
            "match_mode": "exact",
            "pattern": "START",
            "cooldown_ms": 0,
            "reply_delay_ms": reply_delay_ms,
            "replies": ["TEST", "第二条"],
        }
    )


def build_any_group_rule() -> Rule:
    return Rule(
        id="any_group_message",
        enabled=True,
        talker="47561933285@chatroom",
        sender="",
        chat_scope=ChatScope.GROUP,
        message_type=MessageType.UNKNOWN,
        match_mode=MatchMode.ANY,
        pattern="",
        cooldown_ms=0,
        replies=["TEST"],
    )


class ArmedBotTest(unittest.TestCase):
    def test_disarmed_state_blocks_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ArmStateStore(Path(tmp) / "arm_state.json")
            sender = MemorySender()
            dispatcher = SendDispatcher(sender, RuntimeConfig(), logging.getLogger("test"))
            bot = WeChatAutomationBot(
                [build_rule()],
                dispatcher,
                logging.getLogger("test"),
                store,
            )

            bot.process(build_event("evt-1"))

            self.assertEqual(sender.sent, [])

    def test_successful_batch_consumes_budget_and_auto_disarms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ArmStateStore(Path(tmp) / "arm_state.json")
            store.arm(max_triggers=1)
            sender = MemorySender()
            dispatcher = SendDispatcher(sender, RuntimeConfig(), logging.getLogger("test"))
            bot = WeChatAutomationBot(
                [build_rule()],
                dispatcher,
                logging.getLogger("test"),
                store,
            )

            bot.process(build_event("evt-1"))
            bot.process(build_event("evt-2"))

            self.assertEqual(sender.sent, ["TEST", "第二条"])
            self.assertFalse(store.read().enabled)
            self.assertEqual(store.read().reason, "budget_exhausted")

    def test_reply_delay_runs_before_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            calls: list[str] = []
            store = ArmStateStore(Path(tmp) / "arm_state.json")
            store.arm(max_triggers=1)
            sender = MemorySender(calls)
            dispatcher = SendDispatcher(sender, RuntimeConfig(), logging.getLogger("test"))
            bot = WeChatAutomationBot(
                [build_rule(reply_delay_ms=150)],
                dispatcher,
                logging.getLogger("test"),
                store,
                sleeper=lambda seconds: calls.append(f"sleep:{seconds}"),
            )

            bot.process(build_event("evt-1"))

            self.assertEqual(calls[0], "sleep:0.15")
            self.assertEqual(calls[1], "send:TEST")

    def test_arbitrary_trigger_does_not_reply_to_its_own_echo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ArmStateStore(Path(tmp) / "arm_state.json")
            store.arm(max_triggers=5)
            sender = MemorySender()
            dispatcher = SendDispatcher(sender, RuntimeConfig(), logging.getLogger("test"))
            bot = WeChatAutomationBot(
                [build_any_group_rule()],
                dispatcher,
                logging.getLogger("test"),
                store,
            )

            bot.process(build_group_event("incoming", "威士忌Wow", "hello"))
            bot.process(build_group_event("echo", "wxid_w541fvgeqaq922", "TEST"))

            self.assertEqual(sender.sent, ["TEST"])


if __name__ == "__main__":
    unittest.main()
