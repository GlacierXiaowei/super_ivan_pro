from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MatchMode(str, Enum):
    EXACT = "exact"
    CONTAINS = "contains"
    REGEX = "regex"


class MessageType(str, Enum):
    TEXT = "text"
    EMOJI = "emoji"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    FILE = "file"
    LINK = "link"
    UNKNOWN = "unknown"

    @classmethod
    def from_raw(cls, value: Any) -> "MessageType":
        if isinstance(value, MessageType):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            for item in cls:
                if item.value == normalized:
                    return item
        if isinstance(value, int):
            mapping = {
                1: cls.TEXT,
                3: cls.IMAGE,
                34: cls.VOICE,
                43: cls.VIDEO,
                47: cls.EMOJI,
                49: cls.LINK,
            }
            return mapping.get(value, cls.UNKNOWN)
        return cls.UNKNOWN


@dataclass(slots=True)
class MessageEvent:
    seq: str
    timestamp: str
    talker: str
    talker_name: str = ""
    is_chat_room: bool = False
    sender: str = ""
    sender_name: str = ""
    message_type: MessageType = MessageType.UNKNOWN
    content: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MessageEvent":
        return cls(
            seq=str(payload.get("seq") or payload.get("id") or ""),
            timestamp=str(payload.get("timestamp") or payload.get("time") or ""),
            talker=str(payload.get("talker") or ""),
            talker_name=str(payload.get("talkerName") or payload.get("talker_name") or ""),
            is_chat_room=bool(payload.get("isChatRoom") or payload.get("is_chat_room") or False),
            sender=str(payload.get("sender") or ""),
            sender_name=str(payload.get("senderName") or payload.get("sender_name") or ""),
            message_type=MessageType.from_raw(payload.get("type")),
            content=str(payload.get("content") or ""),
            raw=dict(payload.get("raw") or payload),
        )

    @property
    def display_talker(self) -> str:
        return self.talker_name or self.talker

    @property
    def display_sender(self) -> str:
        return self.sender_name or self.sender


@dataclass(slots=True)
class Rule:
    id: str
    enabled: bool
    talker: str
    sender: str
    message_type: MessageType
    match_mode: MatchMode
    pattern: str
    cooldown_ms: int
    replies: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Rule":
        return cls(
            id=str(payload["id"]),
            enabled=bool(payload.get("enabled", True)),
            talker=str(payload.get("talker") or ""),
            sender=str(payload.get("sender") or ""),
            message_type=MessageType.from_raw(payload.get("type", "unknown")),
            match_mode=MatchMode(str(payload.get("match_mode", "exact")).lower()),
            pattern=str(payload.get("pattern") or ""),
            cooldown_ms=int(payload.get("cooldown_ms") or 0),
            replies=[str(item) for item in payload.get("replies") or []],
        )


@dataclass(slots=True)
class RuntimeConfig:
    sender_backend: str = "dry_run"
    dry_run: bool = True
    inter_message_delay_ms: int = 180
    retry_count: int = 1
    log_dir: str = "logs"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RuntimeConfig":
        return cls(
            sender_backend=str(payload.get("sender_backend") or "dry_run"),
            dry_run=bool(payload.get("dry_run", True)),
            inter_message_delay_ms=int(payload.get("inter_message_delay_ms") or 180),
            retry_count=int(payload.get("retry_count") or 1),
            log_dir=str(payload.get("log_dir") or "logs"),
        )


@dataclass(slots=True)
class MatchResult:
    matched: bool
    reason: str
