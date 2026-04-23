from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_STATE: dict[str, Any] = {
    "service_state": "stopped",
    "armed": False,
    "mode": "normal",
    "active_target": {
        "talker": "",
        "display_name": "",
        "is_group": False,
    },
    "recent_events": [],
}


class DesktopStateStore:
    def __init__(self, runtime_root: Path) -> None:
        self._runtime_root = Path(runtime_root)
        self._state_path = self._runtime_root / "config" / "desktop_state.json"

    def load(self) -> dict[str, Any]:
        if not self._state_path.exists():
            self.save(dict(DEFAULT_STATE))
        return json.loads(self._state_path.read_text(encoding="utf-8"))

    def save(self, state: dict[str, Any]) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

