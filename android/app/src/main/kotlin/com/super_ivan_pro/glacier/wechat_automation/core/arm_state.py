from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODE = "armed_current_chat"
DEFAULT_MAX_TRIGGERS = 1


@dataclass(frozen=True, slots=True)
class ArmState:
    enabled: bool
    mode: str
    max_triggers: int
    triggers_sent: int
    reason: str

    @property
    def remaining_triggers(self) -> int | None:
        # Unlimited budget: represent as 0 in storage, but expose None as remaining.
        if self.max_triggers == 0:
            return None
        remaining = self.max_triggers - self.triggers_sent
        return remaining if remaining > 0 else 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": bool(self.enabled),
            "mode": str(self.mode),
            "max_triggers": int(self.max_triggers),
            "triggers_sent": int(self.triggers_sent),
            "remaining_triggers": self.remaining_triggers,
            "reason": str(self.reason),
        }

    @classmethod
    def disarmed_default(cls) -> "ArmState":
        return cls(
            enabled=False,
            mode=DEFAULT_MODE,
            max_triggers=DEFAULT_MAX_TRIGGERS,
            triggers_sent=0,
            reason="not_armed",
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ArmState":
        enabled = bool(payload.get("enabled", False))
        mode = str(payload.get("mode") or DEFAULT_MODE)
        max_triggers_raw = payload.get("max_triggers", DEFAULT_MAX_TRIGGERS)
        triggers_sent_raw = payload.get("triggers_sent", 0)

        try:
            max_triggers = int(max_triggers_raw)
        except (TypeError, ValueError):
            max_triggers = DEFAULT_MAX_TRIGGERS
        if max_triggers < 0:
            max_triggers = 0

        try:
            triggers_sent = int(triggers_sent_raw)
        except (TypeError, ValueError):
            triggers_sent = 0
        if triggers_sent < 0:
            triggers_sent = 0

        reason = str(payload.get("reason") or ("armed" if enabled else "not_armed"))
        return cls(
            enabled=enabled,
            mode=mode,
            max_triggers=max_triggers,
            triggers_sent=triggers_sent,
            reason=reason,
        )


class ArmStateStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def read(self) -> ArmState:
        if not self._path.exists():
            return ArmState.disarmed_default()
        try:
            raw = self._path.read_text(encoding="utf-8").strip()
            if not raw:
                return ArmState.disarmed_default()
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                return ArmState.disarmed_default()
            return ArmState.from_dict(payload)
        except (OSError, json.JSONDecodeError):
            return ArmState.disarmed_default()

    def _write(self, state: ArmState) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def arm(self, *, max_triggers: int) -> ArmState:
        budget = int(max_triggers)
        if budget < 0:
            budget = 0
        state = ArmState(
            enabled=True,
            mode=DEFAULT_MODE,
            max_triggers=budget,
            triggers_sent=0,
            reason="armed",
        )
        self._write(state)
        return state

    def disarm(self, *, reason: str = "not_armed", max_triggers: int | None = None) -> ArmState:
        current = self.read()
        budget = current.max_triggers if current.max_triggers >= 0 else DEFAULT_MAX_TRIGGERS
        triggers_sent = current.triggers_sent if current.triggers_sent >= 0 else 0
        if max_triggers is not None:
            budget = int(max_triggers)
            if budget < 0:
                budget = 0
            if budget != current.max_triggers:
                triggers_sent = 0
        state = ArmState(
            enabled=False,
            mode=current.mode or DEFAULT_MODE,
            max_triggers=budget,
            triggers_sent=triggers_sent,
            reason=reason,
        )
        self._write(state)
        return state

    def record_success(self) -> ArmState:
        current = self.read()
        if not current.enabled:
            return current

        next_sent = current.triggers_sent + 1
        if current.max_triggers == 0:
            # Unlimited budget: never auto-disarm.
            state = ArmState(
                enabled=True,
                mode=current.mode,
                max_triggers=0,
                triggers_sent=next_sent,
                reason=current.reason or "armed",
            )
            self._write(state)
            return state

        exhausted = next_sent >= current.max_triggers
        state = ArmState(
            enabled=not exhausted,
            mode=current.mode,
            max_triggers=current.max_triggers,
            triggers_sent=next_sent,
            reason="budget_exhausted" if exhausted else (current.reason or "armed"),
        )
        self._write(state)
        return state
