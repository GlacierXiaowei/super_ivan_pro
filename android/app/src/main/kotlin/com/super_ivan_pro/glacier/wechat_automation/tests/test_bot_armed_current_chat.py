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
from core.models import MessageEvent, MessageType, Rule, RuntimeConfig  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
