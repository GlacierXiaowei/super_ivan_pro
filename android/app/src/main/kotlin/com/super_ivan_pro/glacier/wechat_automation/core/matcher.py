from __future__ import annotations

import re

from .models import ChatScope, MatchMode, MatchResult, MessageEvent, MessageType, Rule


def _matches_message_type(message: MessageEvent, rule: Rule) -> bool:
    if rule.message_type == MessageType.UNKNOWN:
        return True
    return message.message_type == rule.message_type


def _matches_chat_scope(message: MessageEvent, rule: Rule) -> bool:
    if rule.chat_scope == ChatScope.ANY:
        return True
    if rule.chat_scope == ChatScope.GROUP:
        return message.is_chat_room
    if rule.chat_scope == ChatScope.PRIVATE:
        return not message.is_chat_room
    return False


def match_rule(message: MessageEvent, rule: Rule) -> MatchResult:
    if not rule.enabled:
        return MatchResult(False, "rule_disabled")
    if rule.talker and rule.talker not in {message.talker, message.display_talker}:
        return MatchResult(False, "talker_mismatch")
    if rule.sender and rule.sender not in {message.sender, message.display_sender}:
        return MatchResult(False, "sender_mismatch")
    if not _matches_chat_scope(message, rule):
        return MatchResult(False, "chat_scope_mismatch")
    if not _matches_message_type(message, rule):
        return MatchResult(False, "type_mismatch")
    if rule.match_mode == MatchMode.ANY:
        return MatchResult(True, "matched")

    content = message.content or ""
    pattern = rule.pattern or ""
    if rule.match_mode == MatchMode.EXACT:
        matched = content == pattern
    elif rule.match_mode == MatchMode.CONTAINS:
        matched = pattern in content
    elif rule.match_mode == MatchMode.REGEX:
        matched = re.search(pattern, content) is not None
    else:
        matched = False

    return MatchResult(matched, "matched" if matched else "pattern_mismatch")
