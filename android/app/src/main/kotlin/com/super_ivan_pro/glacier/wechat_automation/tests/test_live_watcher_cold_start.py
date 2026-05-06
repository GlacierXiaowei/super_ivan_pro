from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.models import RuntimeConfig
from core.watcher_adapter import WechatDecryptHistoryWatcher


class StubHistoryWatcher(WechatDecryptHistoryWatcher):
    def __init__(self, responses: list[list[dict]], chat_filter: str = "") -> None:
        super().__init__(RuntimeConfig(), chat_filter=chat_filter)
        self._responses = [list(batch) for batch in responses]
        self.calls: list[dict[str, str]] = []

    def _fetch_history(self, params: dict[str, str]) -> object:
        self.calls.append(dict(params))
        if not self._responses:
            return []
        return self._responses.pop(0)


class LiveWatcherColdStartTest(unittest.TestCase):
    def test_cold_start_skips_existing_history_and_only_fetches_new_events(self) -> None:
        existing_event = {
            "timestamp": 1777539000,
            "chat": "filehelper",
            "username": "filehelper",
            "is_group": False,
            "sender": "",
            "type": "文本",
            "content": "START",
        }
        new_event = {
            "timestamp": 1777539005,
            "chat": "filehelper",
            "username": "filehelper",
            "is_group": False,
            "sender": "",
            "type": "文本",
            "content": "NEXT",
        }
        watcher = StubHistoryWatcher(
            responses=[
                [existing_event],
                [new_event],
            ]
        )

        events = watcher._fetch_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["content"], "NEXT")
        self.assertEqual(
            watcher.calls,
            [
                {"limit": "1"},
                {"since": "1777539000", "limit": "200"},
            ],
        )

    def test_cold_start_and_live_fetch_use_chat_filter_when_configured(self) -> None:
        existing_event = {
            "timestamp": 1777539000,
            "chat": "filehelper",
            "username": "filehelper",
            "is_group": False,
            "sender": "",
            "type": "文本",
            "content": "START",
        }
        new_event = {
            "timestamp": 1777539005,
            "chat": "filehelper",
            "username": "filehelper",
            "is_group": False,
            "sender": "",
            "type": "文本",
            "content": "NEXT",
        }
        watcher = StubHistoryWatcher(
            responses=[
                [existing_event],
                [new_event],
            ],
            chat_filter="filehelper",
        )

        events = watcher._fetch_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["content"], "NEXT")
        self.assertEqual(
            watcher.calls,
            [
                {"limit": "1", "chat": "filehelper"},
                {"since": "1777539000", "limit": "200", "chat": "filehelper"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
