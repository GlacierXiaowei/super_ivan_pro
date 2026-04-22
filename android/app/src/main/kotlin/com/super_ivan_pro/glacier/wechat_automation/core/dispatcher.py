from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from .models import MessageEvent, Rule, RuntimeConfig
from .sender_adapter import Sender


@dataclass(slots=True)
class DispatchReport:
    attempted: int
    sent: int


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

    def dispatch(self, rule: Rule, context: MessageEvent) -> DispatchReport:
        sent = 0
        for index, reply in enumerate(rule.replies, start=1):
            self._send_with_retry(context, reply, rule.id, index)
            sent += 1
            if index != len(rule.replies):
                time.sleep(self._runtime.inter_message_delay_ms / 1000.0)
        return DispatchReport(attempted=len(rule.replies), sent=sent)

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
