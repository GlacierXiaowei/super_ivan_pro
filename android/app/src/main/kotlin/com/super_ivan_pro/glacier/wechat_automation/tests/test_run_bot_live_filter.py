from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.models import ChatScope, MatchMode, MessageType, Rule
from scripts import run_bot


def _rule(rule_id: str, talker: str, enabled: bool = True) -> Rule:
    return Rule(
        id=rule_id,
        enabled=enabled,
        talker=talker,
        sender="",
        chat_scope=ChatScope.ANY,
        message_type=MessageType.TEXT,
        match_mode=MatchMode.EXACT,
        pattern="START",
        cooldown_ms=0,
        replies=["TEST"],
    )


class RunBotLiveFilterTest(unittest.TestCase):
    def test_uses_unique_enabled_rule_talker_as_live_chat_filter(self) -> None:
        live_chat_filter_for_rules = getattr(run_bot, "_live_chat_filter_for_rules", None)

        self.assertIsNotNone(live_chat_filter_for_rules)
        self.assertEqual(
            live_chat_filter_for_rules(
                [
                    _rule("disabled", "ignored", enabled=False),
                    _rule("active", "filehelper"),
                ]
            ),
            "filehelper",
        )

    def test_disables_live_chat_filter_when_enabled_rules_have_multiple_talkers(self) -> None:
        live_chat_filter_for_rules = getattr(run_bot, "_live_chat_filter_for_rules", None)

        self.assertIsNotNone(live_chat_filter_for_rules)
        self.assertEqual(
            live_chat_filter_for_rules(
                [
                    _rule("one", "filehelper"),
                    _rule("two", "47561933285@chatroom"),
                ]
            ),
            "",
        )

    def test_disables_live_chat_filter_when_any_enabled_rule_has_no_talker(self) -> None:
        live_chat_filter_for_rules = getattr(run_bot, "_live_chat_filter_for_rules", None)

        self.assertIsNotNone(live_chat_filter_for_rules)
        self.assertEqual(
            live_chat_filter_for_rules(
                [
                    _rule("targeted", "filehelper"),
                    _rule("wildcard", ""),
                ]
            ),
            "",
        )


if __name__ == "__main__":
    unittest.main()
