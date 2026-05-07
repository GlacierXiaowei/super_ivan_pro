from __future__ import annotations

import json
import logging
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
    STREAM_RETRY_DELAY_SECONDS = 2.0

    def __init__(self, runtime: RuntimeConfig, chat_filter: str = "", prefer_stream: bool = True) -> None:
        self._base_url = runtime.watcher_url.rstrip("/")
        self._poll_interval_sec = max(runtime.poll_interval_ms, 20) / 1000.0
        self._history_limit = max(runtime.history_limit, 10)
        self._chat_filter = chat_filter.strip()
        self._prefer_stream = prefer_stream
        self._logger = logging.getLogger("wechat_automation")
        self._since_timestamp = 0
        self._seen_keys: set[str] = set()
        self._bootstrapped = False

    def iter_events(self) -> Iterator[MessageEvent]:
        stream_retry_at = 0.0
        while True:
            if self._prefer_stream and time.monotonic() >= stream_retry_at:
                try:
                    yield from self._iter_stream_events()
                except Exception as exc:
                    self._logger.warning("watcher_stream_error error=%s", exc)
                    stream_retry_at = time.monotonic() + self.STREAM_RETRY_DELAY_SECONDS

            events = self._fetch_events()
            if not events:
                time.sleep(self._poll_interval_sec)
                continue

            for payload in events:
                event = self._accept_payload(payload, source="history")
                if not event:
                    continue
                yield event

            time.sleep(self._poll_interval_sec)

    def _fetch_events(self) -> list[dict]:
        if not self._bootstrapped:
            self._prime_since_timestamp()
        started = time.perf_counter()
        payload = self._fetch_history(
            self._history_params(
                {
                    "since": str(self._since_timestamp),
                    "limit": str(self._history_limit),
                }
            )
        )
        if not isinstance(payload, list):
            return []
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        self._logger.info(
            "watcher_history_fetch elapsed_ms=%s count=%s since=%s limit=%s chat_filter=%s",
            elapsed_ms,
            len(payload),
            self._since_timestamp,
            self._history_limit,
            self._chat_filter,
        )
        if payload:
            latest_ts = max(int(item.get("timestamp", 0) or 0) for item in payload)
            self._since_timestamp = max(self._since_timestamp, latest_ts)
        return [item for item in payload if isinstance(item, dict)]

    def _iter_stream_events(self) -> Iterator[MessageEvent]:
        if not self._bootstrapped:
            self._prime_since_timestamp()

        with self._open_stream() as response:
            self._logger.info(
                "watcher_stream_connect url=%s chat_filter=%s",
                f"{self._base_url}/stream",
                self._chat_filter,
            )
            for payload in self._fetch_events():
                event = self._accept_payload(payload, source="history_catchup")
                if event is not None:
                    yield event
            yield from self._iter_stream_response_events(response)

    def _iter_stream_response_events(self, response: Iterable[bytes]) -> Iterator[MessageEvent]:
        event_type = ""
        data_lines: list[str] = []
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
            if not line:
                payload = self._stream_payload(event_type, data_lines)
                event_type = ""
                data_lines = []
                if payload is None:
                    continue
                event = self._accept_payload(payload, source="stream")
                if event is not None:
                    yield event
                continue
            if line.startswith(":"):
                continue
            if line.startswith("event:"):
                event_type = line[6:].strip()
                continue
            if line.startswith("data:"):
                data_lines.append(line[5:].lstrip())

    def _open_stream(self):
        url = f"{self._base_url}/stream"
        return urllib.request.urlopen(url, timeout=30)

    def _iter_stream_lines(self) -> Iterator[bytes]:
        with self._open_stream() as response:
            yield from response

    @staticmethod
    def _stream_payload(event_type: str, data_lines: list[str]) -> dict | None:
        if event_type:
            return None
        if not data_lines:
            return None
        payload = json.loads("\n".join(data_lines))
        if not isinstance(payload, dict):
            return None
        return payload

    def _accept_payload(self, payload: dict, source: str) -> MessageEvent | None:
        if self._chat_filter and not self._payload_matches_chat_filter(payload):
            return None
        event = self._normalize_payload(payload)
        if not event:
            return None
        dedupe_key = self._dedupe_key(payload)
        if dedupe_key in self._seen_keys:
            return None
        self._seen_keys.add(dedupe_key)

        timestamp = int(payload.get("timestamp", 0) or 0)
        self._since_timestamp = max(self._since_timestamp, timestamp)
        self._logger.info(
            "watcher_event source=%s seq=%s lag_ms=%s talker=%s sender=%s",
            source,
            event.seq,
            self._event_lag_ms(timestamp),
            event.display_talker,
            event.display_sender,
        )
        return event

    def _payload_matches_chat_filter(self, payload: dict) -> bool:
        needle = self._chat_filter.lower()
        return (
            needle in str(payload.get("chat", "")).lower()
            or needle in str(payload.get("username", "")).lower()
        )

    @staticmethod
    def _event_lag_ms(timestamp: int) -> int:
        if timestamp <= 0:
            return 0
        return max(int((time.time() - timestamp) * 1000), 0)

    def _prime_since_timestamp(self) -> None:
        payload = self._fetch_history(self._history_params({"limit": "1"}))
        self._bootstrapped = True
        if not isinstance(payload, list) or not payload:
            return

        latest_ts = max(int(item.get("timestamp", 0) or 0) for item in payload if isinstance(item, dict))
        self._since_timestamp = max(self._since_timestamp, latest_ts)

    def _history_params(self, params: dict[str, str]) -> dict[str, str]:
        if self._chat_filter:
            return {**params, "chat": self._chat_filter}
        return params

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
