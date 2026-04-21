from __future__ import annotations

import logging
import time

from .models import MessageEvent, Rule, RuntimeConfig
from .sender_adapter import Sender


class SendDispatcher:
    def __init__(
        self,
        sender: Sender,
        runtime: RuntimeConfig,
        logger: logging.Logger,
    ) -> None:
        self._sender = sender
        self._runtime = runtime
        self._logger = logger

    def dispatch(self, rule: Rule, context: MessageEvent) -> None:
        for index, reply in enumerate(rule.replies, start=1):
            self._send_with_retry(context, reply, rule.id, index)
            if index != len(rule.replies):
                time.sleep(self._runtime.inter_message_delay_ms / 1000.0)

    def _send_with_retry(
        self,
        context: MessageEvent,
        message: str,
        rule_id: str,
        index: int,
    ) -> None:
        attempts = max(self._runtime.retry_count, 0) + 1
        for attempt in range(1, attempts + 1):
            try:
                self._sender.send_text(context, message)
                self._logger.info(
                    "dispatch_success rule=%s attempt=%s reply_index=%s",
                    rule_id,
                    attempt,
                    index,
                )
                return
            except Exception:
                self._logger.exception(
                    "dispatch_failure rule=%s attempt=%s reply_index=%s",
                    rule_id,
                    attempt,
                    index,
                )
                if attempt == attempts:
                    raise
