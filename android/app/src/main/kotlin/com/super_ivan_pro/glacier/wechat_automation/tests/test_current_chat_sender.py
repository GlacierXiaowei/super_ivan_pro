from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.current_chat_sender import (  # noqa: E402
    CurrentChatSender,
    FastClipboardInputDriver,
    WindowSnapshot,
)
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


class SequenceFocusProvider:
    def __init__(self, controls: list[object]) -> None:
        self._controls = list(controls)
        self._last = controls[-1]

    def get_focused_control(self) -> object:
        if self._controls:
            self._last = self._controls.pop(0)
        return self._last


class DummyInputDriver:
    def __init__(self) -> None:
        self.sent: list[tuple[object, str]] = []

    def send_text(self, control: object, text: str) -> bool:
        self.sent.append((control, text))
        return True


class DummyControl:
    def __init__(self, control_type: str = "EditControl") -> None:
        self.ControlTypeName = control_type


class DummyChatInputFinder:
    def __init__(self, control: object | None) -> None:
        self._control = control

    def find_chat_input(self, window: WindowSnapshot) -> object | None:
        return self._control


class SequenceChatInputFinder:
    def __init__(self, controls: list[object | None]) -> None:
        self._controls = list(controls)
        self._last = controls[-1] if controls else None

    def find_chat_input(self, window: WindowSnapshot) -> object | None:
        if self._controls:
            self._last = self._controls.pop(0)
        return self._last


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
        focused_control = DummyControl()
        sender = CurrentChatSender(
            logger=logging.getLogger("test"),
            window_inspector=DummyWindowInspector(
                WindowSnapshot(hwnd=1, title="微信", class_name="WeChatMainWndForPC")
            ),
            focus_provider=DummyFocusProvider(focused_control),
            input_driver=driver,
        )

        sender.send_text(build_event(), "TEST")

        self.assertEqual(driver.sent, [(focused_control, "TEST")])

    def test_auto_finds_chat_input_when_focus_is_not_editable(self) -> None:
        driver = DummyInputDriver()
        found_control = DummyControl()
        sender = CurrentChatSender(
            logger=logging.getLogger("test"),
            window_inspector=DummyWindowInspector(
                WindowSnapshot(hwnd=1, title="微信", class_name="WeChatMainWndForPC")
            ),
            focus_provider=DummyFocusProvider(DummyControl("ButtonControl")),
            input_driver=driver,
            chat_input_finder=DummyChatInputFinder(found_control),
        )

        sender.send_text(build_event(), "TEST")

        self.assertEqual(driver.sent, [(found_control, "TEST")])

    def test_fails_when_focus_is_not_editable_and_chat_input_cannot_be_found(self) -> None:
        sender = CurrentChatSender(
            logger=logging.getLogger("test"),
            window_inspector=DummyWindowInspector(
                WindowSnapshot(hwnd=1, title="微信", class_name="WeChatMainWndForPC")
            ),
            focus_provider=DummyFocusProvider(DummyControl("ButtonControl")),
            input_driver=DummyInputDriver(),
            chat_input_finder=DummyChatInputFinder(None),
        )

        with self.assertRaisesRegex(RuntimeError, "chat_input_not_found"):
            sender.send_text(build_event(), "TEST")

    def test_retries_chat_input_lookup_within_second_send(self) -> None:
        driver = DummyInputDriver()
        focused_control = DummyControl()
        recovered_control = DummyControl()
        sender = CurrentChatSender(
            logger=logging.getLogger("test"),
            window_inspector=DummyWindowInspector(
                WindowSnapshot(hwnd=1, title="微信", class_name="WeChatMainWndForPC")
            ),
            focus_provider=SequenceFocusProvider(
                [focused_control, DummyControl("ButtonControl"), DummyControl("ButtonControl")]
            ),
            input_driver=driver,
            chat_input_finder=SequenceChatInputFinder([None, recovered_control]),
        )

        sender.send_text(build_event(), "TEST-1")
        sender.send_text(build_event(), "TEST-2")

        self.assertEqual(
            driver.sent,
            [
                (focused_control, "TEST-1"),
                (recovered_control, "TEST-2"),
            ],
        )

    def test_strict_focus_mode_fails_without_editable_focus(self) -> None:
        sender = CurrentChatSender(
            logger=logging.getLogger("test"),
            window_inspector=DummyWindowInspector(
                WindowSnapshot(hwnd=1, title="微信", class_name="WeChatMainWndForPC")
            ),
            focus_provider=DummyFocusProvider(DummyControl("ButtonControl")),
            input_driver=DummyInputDriver(),
            chat_input_finder=DummyChatInputFinder(DummyControl()),
            require_focused_edit=True,
        )

        with self.assertRaisesRegex(RuntimeError, "chat_input_not_focused"):
            sender.send_text(build_event(), "TEST")

    def test_fast_clipboard_driver_uses_direct_hotkeys(self) -> None:
        actions: list[str] = []
        driver = FastClipboardInputDriver(
            logger=logging.getLogger("test"),
            clipboard_setter=lambda text: actions.append(f"clipboard:{text}") or True,
            key_sender=lambda action: actions.append(action),
        )

        sent = driver.send_text(DummyControl(), "TEST")

        self.assertTrue(sent)
        self.assertEqual(
            actions,
            [
                "clipboard:TEST",
                "ctrl+a",
                "delete",
                "ctrl+v",
                "enter",
            ],
        )


if __name__ == "__main__":
    unittest.main()
