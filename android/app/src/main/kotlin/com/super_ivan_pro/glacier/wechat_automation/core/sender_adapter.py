from __future__ import annotations

import logging
from typing import Protocol

from .models import MessageEvent, RuntimeConfig


class Sender(Protocol):
    def send_text(self, context: MessageEvent, message: str) -> None:
        ...


class DryRunSender:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def send_text(self, context: MessageEvent, message: str) -> None:
        self._logger.info(
            "dry_run_send talker=%s sender=%s payload=%s",
            context.display_talker,
            context.display_sender,
            message,
        )


class Wx4pySender:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        try:
            from wx4py import WeChatClient  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "wx4py backend requested but wx4py is not installed."
            ) from exc
        self._client_cls = WeChatClient

    def send_text(self, context: MessageEvent, message: str) -> None:
        target_name = context.display_talker
        target_type = "group" if context.is_chat_room else "contact"
        with self._client_cls(auto_connect=True) as wx:
            wx.chat_window.send_to(target_name, message, target_type=target_type)
        self._logger.info(
            "wx4py_send talker=%s target_type=%s payload=%s",
            target_name,
            target_type,
            message,
        )


def create_sender(runtime: RuntimeConfig, logger: logging.Logger) -> Sender:
    backend = runtime.sender_backend.lower().strip()
    if runtime.dry_run or backend == "dry_run":
        return DryRunSender(logger)
    if backend == "wx4py":
        return Wx4pySender(logger)
    raise ValueError(f"Unsupported sender backend: {runtime.sender_backend}")
