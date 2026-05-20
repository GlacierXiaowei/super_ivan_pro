from __future__ import annotations

import logging
import time
from typing import Callable

from .arm_state import ArmStateStore
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
        arm_state_store: ArmStateStore,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._rules = rules
        self._dispatcher = dispatcher
        self._logger = logger
        self._arm_state_store = arm_state_store
        self._sleeper = sleeper
        self._clock = clock
        self._deduper = SequenceDeduper()
        self._cooldown = CooldownGate()
        self._sent_echoes: list[tuple[float, str, str, str]] = []

    def process(self, event: MessageEvent) -> None:
        self._logger.info(
            "event_received seq=%s talker=%s sender=%s type=%s content=%s",
            event.seq,
            event.display_talker,
            event.display_sender,
            event.message_type.value,
            event.content,
        )
        if self._consume_sent_echo(event):
            self._logger.info("event_skip seq=%s reason=sent_echo", event.seq)
            return

        state = self._arm_state_store.read()
        if not state.enabled:
            self._logger.info(
                "event_skip seq=%s reason=not_armed state_reason=%s",
                event.seq,
                state.reason,
            )
            return

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
            if rule.reply_delay_ms > 0:
                self._logger.info(
                    "reply_delay_start rule=%s seq=%s delay_ms=%s",
                    rule.id,
                    event.seq,
                    rule.reply_delay_ms,
                )
                self._sleeper(rule.reply_delay_ms / 1000.0)
                delayed_state = self._arm_state_store.read()
                if not delayed_state.enabled:
                    self._logger.info(
                        "event_skip seq=%s reason=not_armed_after_delay state_reason=%s",
                        event.seq,
                        delayed_state.reason,
                    )
                    return
            try:
                report = self._dispatcher.dispatch(rule, event)
            except Exception as exc:
                self._logger.error(
                    "dispatch_aborted rule=%s seq=%s error=%s",
                    rule.id,
                    event.seq,
                    exc,
                )
                return
            self._remember_sent_echoes(rule, event, report.sent)
            if report.sent == len(rule.replies):
                updated = self._arm_state_store.record_success()
                self._logger.info(
                    "armed_state_update enabled=%s sent=%s remaining=%s reason=%s",
                    updated.enabled,
                    updated.triggers_sent,
                    updated.remaining_triggers,
                    updated.reason,
                )

    def _consume_sent_echo(self, event: MessageEvent) -> bool:
        now = self._clock()
        self._sent_echoes = [item for item in self._sent_echoes if item[0] >= now]
        for index, (_deadline, talker, content, source_sender) in enumerate(self._sent_echoes):
            if event.talker != talker or event.content != content:
                continue
            if source_sender and event.sender == source_sender:
                continue
            del self._sent_echoes[index]
            return True
        return False

    def _remember_sent_echoes(self, rule: Rule, event: MessageEvent, sent_count: int) -> None:
        if sent_count <= 0:
            return
        deadline = self._clock() + 10.0
        for reply in rule.replies[:sent_count]:
            self._sent_echoes.append((deadline, event.talker, reply, event.sender))
        self._sent_echoes = self._sent_echoes[-50:]
