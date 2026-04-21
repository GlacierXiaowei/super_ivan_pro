from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator, Protocol

from .models import MessageEvent


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
