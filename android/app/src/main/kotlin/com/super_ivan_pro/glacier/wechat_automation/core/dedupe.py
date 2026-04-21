from __future__ import annotations

import time
from collections import deque


class SequenceDeduper:
    def __init__(self, max_size: int = 2048) -> None:
        self._max_size = max_size
        self._queue: deque[str] = deque()
        self._seen: set[str] = set()

    def already_seen(self, key: str) -> bool:
        return key in self._seen

    def mark_seen(self, key: str) -> None:
        if key in self._seen:
            return
        self._queue.append(key)
        self._seen.add(key)
        while len(self._queue) > self._max_size:
            expired = self._queue.popleft()
            self._seen.discard(expired)


class CooldownGate:
    def __init__(self) -> None:
        self._last_seen_ms: dict[str, int] = {}

    def allow(self, key: str, cooldown_ms: int, now_ms: int | None = None) -> bool:
        now = now_ms if now_ms is not None else int(time.time() * 1000)
        previous = self._last_seen_ms.get(key)
        if previous is None or cooldown_ms <= 0:
            self._last_seen_ms[key] = now
            return True
        if now - previous >= cooldown_ms:
            self._last_seen_ms[key] = now
            return True
        return False
