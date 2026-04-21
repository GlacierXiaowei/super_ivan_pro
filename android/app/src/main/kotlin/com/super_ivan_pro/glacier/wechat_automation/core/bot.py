from __future__ import annotations

import logging

from .dedupe import CooldownGate, SequenceDeduper
from .dispatcher import SendDispatcher
from .matcher import match_rule
from .models import MessageEvent, Rule


class WeChatAutomationBot:
    def __init__(
        self,
        rules: list[Rule],
        dispatcher: SendDispatcher,
        logger: logging.Logger,
    ) -> None:
        self._rules = rules
        self._dispatcher = dispatcher
        self._logger = logger
        self._deduper = SequenceDeduper()
        self._cooldown = CooldownGate()

    def process(self, event: MessageEvent) -> None:
        self._logger.info(
            "event_received seq=%s talker=%s sender=%s type=%s content=%s",
            event.seq,
            event.display_talker,
            event.display_sender,
            event.message_type.value,
            event.content,
        )
        for rule in self._rules:
            result = match_rule(event, rule)
            if not result.matched:
                self._logger.info(
                    "rule_skip rule=%s seq=%s reason=%s",
                    rule.id,
                    event.seq,
                    result.reason,
                )
                continue

            dedupe_key = f"{rule.id}:{event.seq}"
            if self._deduper.already_seen(dedupe_key):
                self._logger.info("rule_skip rule=%s seq=%s reason=duplicate", rule.id, event.seq)
                continue

            cooldown_key = f"{rule.id}:{event.talker}:{event.sender}:{rule.pattern}"
            if not self._cooldown.allow(cooldown_key, rule.cooldown_ms):
                self._logger.info("rule_skip rule=%s seq=%s reason=cooldown", rule.id, event.seq)
                continue

            self._deduper.mark_seen(dedupe_key)
            self._logger.info("rule_match rule=%s seq=%s", rule.id, event.seq)
            self._dispatcher.dispatch(rule, event)
