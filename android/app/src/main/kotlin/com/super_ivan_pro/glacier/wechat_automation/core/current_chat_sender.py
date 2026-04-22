from __future__ import annotations

import ctypes
import logging
from dataclasses import dataclass
from typing import Protocol

from .models import MessageEvent


@dataclass(slots=True)
class WindowSnapshot:
    hwnd: int
    title: str
    class_name: str

    @property
    def looks_like_wechat(self) -> bool:
        title = self.title or ""
        class_name = self.class_name or ""
        return "微信" in title or "WeChat" in title or "WeChat" in class_name


class WindowInspector(Protocol):
    def snapshot(self) -> WindowSnapshot:
        ...


class FocusProvider(Protocol):
    def get_focused_control(self) -> object:
        ...


class InputDriver(Protocol):
    def send_text(self, control: object, text: str) -> bool:
        ...


class Win32WindowInspector:
    def snapshot(self) -> WindowSnapshot:
        user32 = ctypes.windll.user32
        hwnd = int(user32.GetForegroundWindow())
        title_buffer = ctypes.create_unicode_buffer(512)
        class_buffer = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title_buffer, len(title_buffer))
        user32.GetClassNameW(hwnd, class_buffer, len(class_buffer))
        return WindowSnapshot(
            hwnd=hwnd,
            title=title_buffer.value,
            class_name=class_buffer.value,
        )


class Wx4pyFocusProvider:
    def get_focused_control(self) -> object:
        from wx4py.core import uiautomation as auto

        return auto.GetFocusedControl()


class Wx4pyInputDriver:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def send_text(self, control: object, text: str) -> bool:
        from wx4py.features.chat import ChatWindow

        return ChatWindow.send_text_via_input(
            control,
            text,
            logger_override=self._logger,
        )


class CurrentChatSender:
    def __init__(
        self,
        logger: logging.Logger,
        window_inspector: WindowInspector | None = None,
        focus_provider: FocusProvider | None = None,
        input_driver: InputDriver | None = None,
    ) -> None:
        self._logger = logger
        self._window_inspector = window_inspector or Win32WindowInspector()
        self._focus_provider = focus_provider or Wx4pyFocusProvider()
        self._input_driver = input_driver or Wx4pyInputDriver(logger)

    def send_text(self, context: MessageEvent, message: str) -> None:
        window = self._window_inspector.snapshot()
        if not window.looks_like_wechat:
            raise RuntimeError("foreground_not_wechat")

        control = self._focus_provider.get_focused_control()
        if control is None:
            raise RuntimeError("focused_control_missing")

        control_type = str(getattr(control, "ControlTypeName", "") or "")
        if control_type not in {"EditControl", "DocumentControl"}:
            raise RuntimeError("focused_control_not_editable")

        if not self._input_driver.send_text(control, message):
            raise RuntimeError("current_chat_send_failed")

        self._logger.info(
            "current_chat_send talker=%s sender=%s payload=%s",
            context.display_talker,
            context.display_sender,
            message,
        )
