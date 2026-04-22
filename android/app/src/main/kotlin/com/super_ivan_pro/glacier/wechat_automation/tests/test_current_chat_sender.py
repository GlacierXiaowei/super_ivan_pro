from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.current_chat_sender import CurrentChatSender, WindowSnapshot  # noqa: E402
from core.models import MessageEvent, MessageType  # noqa: E402


class DummyWindowInspector:
    def __init__(self, snapshot: WindowSnapshot) -> None:
        self._snapshot = snapshot

    def snapshot(self) -> WindowSnapshot:
        return self._snapshot


class DummyFocusProvider:
    def __init__(self, control: object) -> None:
        self._control = control

    def get_focused_control(self) -> object:
        return self._control


class DummyInputDriver:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def send_text(self, control: object, text: str) -> bool:
        self.sent.append(text)
        return True


class DummyControl:
    ControlTypeName = "EditControl"


def build_event() -> MessageEvent:
    return MessageEvent(
        seq="evt",
        timestamp="1",
        talker="filehelper",
        talker_name="文件传输助手",
        is_chat_room=False,
        sender="",
        sender_name="",
        message_type=MessageType.TEXT,
        content="START",
    )


class CurrentChatSenderTest(unittest.TestCase):
    def test_rejects_non_wechat_foreground_window(self) -> None:
        sender = CurrentChatSender(
            logger=logging.getLogger("test"),
            window_inspector=DummyWindowInspector(
                WindowSnapshot(hwnd=1, title="记事本", class_name="Notepad")
            ),
            focus_provider=DummyFocusProvider(DummyControl()),
            input_driver=DummyInputDriver(),
        )

        with self.assertRaisesRegex(RuntimeError, "foreground_not_wechat"):
            sender.send_text(build_event(), "TEST")

    def test_sends_when_wechat_window_and_edit_focus_are_ready(self) -> None:
        driver = DummyInputDriver()
        sender = CurrentChatSender(
            logger=logging.getLogger("test"),
            window_inspector=DummyWindowInspector(
                WindowSnapshot(hwnd=1, title="微信", class_name="WeChatMainWndForPC")
            ),
            focus_provider=DummyFocusProvider(DummyControl()),
            input_driver=driver,
        )

        sender.send_text(build_event(), "TEST")

        self.assertEqual(driver.sent, ["TEST"])


if __name__ == "__main__":
    unittest.main()
