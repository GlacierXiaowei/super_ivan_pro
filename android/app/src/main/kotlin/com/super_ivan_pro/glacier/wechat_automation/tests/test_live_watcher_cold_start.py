from __future__ import annotations

import json
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


class FakeStreamResponse:
    def __init__(self, lines: list[bytes]) -> None:
        self._lines = lines

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        return None

    def __iter__(self):
        return iter(self._lines)


class StreamWatcher(StubHistoryWatcher):
    def __init__(
        self,
        responses: list[list[dict]],
        stream_lines: list[bytes],
        chat_filter: str = "",
    ) -> None:
        super().__init__(responses, chat_filter=chat_filter)
        self._stream_lines = list(stream_lines)

    def _iter_stream_lines(self):
        yield from self._stream_lines

    def _open_stream(self):
        return FakeStreamResponse(self._stream_lines)


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

    def test_stream_yields_matching_messages_without_waiting_for_history_poll(self) -> None:
        existing_event = {
            "timestamp": 1777539000,
            "chat": "filehelper",
            "username": "filehelper",
            "is_group": False,
            "sender": "",
            "type": "文本",
            "content": "START",
        }
        matching_event = {
            "timestamp": 1777539001,
            "chat": "filehelper",
            "username": "filehelper",
            "is_group": False,
            "sender": "",
            "type": "文本",
            "content": "NEXT",
        }
        other_chat_event = {
            "timestamp": 1777539002,
            "chat": "other",
            "username": "other",
            "is_group": False,
            "sender": "",
            "type": "文本",
            "content": "NOPE",
        }
        rich_update_event = {
            "event": "rich_update",
            "timestamp": 1777539001,
            "username": "filehelper",
            "rich": {"type": "link"},
        }
        watcher = StreamWatcher(
            responses=[[existing_event]],
            stream_lines=[
                b"event: rich_update\n",
                f"data: {json.dumps(rich_update_event)}\n".encode("utf-8"),
                b"\n",
                f"data: {json.dumps(other_chat_event)}\n".encode("utf-8"),
                b"\n",
                f"data: {json.dumps(matching_event)}\n".encode("utf-8"),
                b"\n",
            ],
            chat_filter="filehelper",
        )

        stream = watcher._iter_stream_events()
        event = next(stream)

        self.assertEqual(event.content, "NEXT")
        self.assertEqual(
            watcher.calls,
            [
                {"limit": "1", "chat": "filehelper"},
                {"since": "1777539000", "limit": "200", "chat": "filehelper"},
            ],
        )

    def test_stream_catches_messages_written_between_prime_and_connected_stream(self) -> None:
        existing_event = {
            "timestamp": 1777539000,
            "chat": "filehelper",
            "username": "filehelper",
            "is_group": False,
            "sender": "",
            "type": "文本",
            "content": "START",
        }
        gap_event = {
            "timestamp": 1777539001,
            "chat": "filehelper",
            "username": "filehelper",
            "is_group": False,
            "sender": "",
            "type": "文本",
            "content": "GAP",
        }
        watcher = StreamWatcher(
            responses=[
                [existing_event],
                [gap_event],
            ],
            stream_lines=[
                b": hb\n",
                b"\n",
            ],
            chat_filter="filehelper",
        )

        stream = watcher._iter_stream_events()
        event = next(stream)

        self.assertEqual(event.content, "GAP")
        self.assertEqual(
            watcher.calls,
            [
                {"limit": "1", "chat": "filehelper"},
                {"since": "1777539000", "limit": "200", "chat": "filehelper"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
