from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from hashlib import sha1
from pathlib import Path
from typing import Iterable, Iterator, Protocol

from .models import MessageEvent, MessageType, RuntimeConfig


class Watcher(Protocol):
    def iter_events(self) -> Iterable[MessageEvent]:
        ...


class JsonlReplayWatcher:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path).resolve()

    def iter_events(self) -> Iterator[MessageEvent]:
        with self._path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                payload = json.loads(stripped)
                yield MessageEvent.from_dict(payload)


class WechatDecryptHistoryWatcher:
    def __init__(self, runtime: RuntimeConfig) -> None:
        self._base_url = runtime.watcher_url.rstrip("/")
        self._poll_interval_sec = max(runtime.poll_interval_ms, 50) / 1000.0
        self._history_limit = max(runtime.history_limit, 10)
        self._since_timestamp = 0
        self._seen_keys: set[str] = set()
        self._bootstrapped = False

    def iter_events(self) -> Iterator[MessageEvent]:
        while True:
            events = self._fetch_events()
            if not events:
                time.sleep(self._poll_interval_sec)
                continue

            for payload in events:
                event = self._normalize_payload(payload)
                if not event:
                    continue
                dedupe_key = self._dedupe_key(payload)
                if dedupe_key in self._seen_keys:
                    continue
                self._seen_keys.add(dedupe_key)
                yield event

            time.sleep(self._poll_interval_sec)

    def _fetch_events(self) -> list[dict]:
        if not self._bootstrapped:
            self._prime_since_timestamp()
        payload = self._fetch_history(
            {
                "since": str(self._since_timestamp),
                "limit": str(self._history_limit),
            }
        )
        if not isinstance(payload, list):
            return []
        if payload:
            latest_ts = max(int(item.get("timestamp", 0) or 0) for item in payload)
            self._since_timestamp = max(self._since_timestamp, latest_ts)
        return [item for item in payload if isinstance(item, dict)]

    def _prime_since_timestamp(self) -> None:
        payload = self._fetch_history({"limit": "1"})
        self._bootstrapped = True
        if not isinstance(payload, list) or not payload:
            return

        latest_ts = max(int(item.get("timestamp", 0) or 0) for item in payload if isinstance(item, dict))
        self._since_timestamp = max(self._since_timestamp, latest_ts)

    def fetch_recent_events(self, limit: int = 50, chat: str = "") -> list[MessageEvent]:
        params = {
            "limit": str(max(limit, 1)),
        }
        if chat:
            params["chat"] = chat
        payload = self._fetch_history(params)
        if not isinstance(payload, list):
            return []
        return self.normalize_payloads([item for item in payload if isinstance(item, dict)])

    def normalize_payloads(self, payloads: list[dict]) -> list[MessageEvent]:
        events: list[MessageEvent] = []
        for payload in payloads:
            event = self._normalize_payload(payload)
            if event:
                events.append(event)
        return events

    def _fetch_history(self, params: dict[str, str]) -> object:
        query = urllib.parse.urlencode(params)
        url = f"{self._base_url}/api/history?{query}"
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def _normalize_payload(self, payload: dict) -> MessageEvent | None:
        timestamp = int(payload.get("timestamp", 0) or 0)
        talker = str(payload.get("chat") or payload.get("username") or "")
        raw_type = payload.get("type")
        content = str(payload.get("content") or "")
        if not talker:
            return None

        type_mapping = {
            "文本": MessageType.TEXT,
            "图片": MessageType.IMAGE,
            "表情": MessageType.EMOJI,
            "语音": MessageType.VOICE,
            "视频": MessageType.VIDEO,
            "链接/文件": MessageType.LINK,
        }
        message_type = type_mapping.get(str(raw_type), MessageType.UNKNOWN)
        seq = self._dedupe_key(payload)
        talker_name = self._display_talker_name(talker)

        return MessageEvent(
            seq=seq,
            timestamp=str(timestamp),
            talker=talker,
            talker_name=talker_name,
            is_chat_room=bool(payload.get("is_group", False)),
            sender=str(payload.get("sender") or ""),
            sender_name=str(payload.get("sender") or ""),
            message_type=message_type,
            content=content,
            raw=dict(payload),
        )

    @staticmethod
    def _display_talker_name(talker: str) -> str:
        if talker == "filehelper":
            return "文件传输助手"
        return talker

    @staticmethod
    def _dedupe_key(payload: dict) -> str:
        base = "|".join(
            [
                str(payload.get("timestamp", "")),
                str(payload.get("username", "")),
                str(payload.get("chat", "")),
                str(payload.get("sender", "")),
                str(payload.get("type", "")),
                str(payload.get("content", "")),
            ]
        )
        return sha1(base.encode("utf-8")).hexdigest()
