# WeChat Armed Current-Chat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an `armed_current_chat` mode that listens for the configured trigger and, when manually armed, sends the configured reply batch immediately into the already-open current WeChat chat.

**Architecture:** Keep the existing `wechat-decrypt` live watcher, matcher, dedupe, and serial dispatcher. Add a file-backed arm/disarm state store that the bot re-reads for each event, count only successful reply batches against the trigger budget, and introduce a lightweight current-chat sender that validates the foreground WeChat window and focused input without using `WeChatClient.connect()`.

**Tech Stack:** Python 3.10, existing standalone `wechat_automation` module, `wx4py.core.uiautomation`, Flask web console, local JSON config/state files, `unittest`

---

**Working directory for every command below:** `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation`

### Task 1: Add File-Backed Armed State And Runtime Config

**Files:**
- Create: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\core\arm_state.py`
- Create: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\config\arm_state.example.json`
- Create: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\config\arm_state.local.json`
- Create: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\tests\test_arm_state_store.py`
- Modify: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\core\models.py`
- Modify: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\config\runtime.example.json`
- Modify: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\config\runtime.local.json`

- [ ] **Step 1: Write the failing armed-state persistence tests**

```python
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.arm_state import ArmStateStore


class ArmStateStoreTest(unittest.TestCase):
    def test_missing_file_defaults_to_disarmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "arm_state.json"
            store = ArmStateStore(path)

            state = store.read()

            self.assertFalse(state.enabled)
            self.assertEqual(state.mode, "armed_current_chat")
            self.assertIsNone(state.max_triggers)
            self.assertEqual(state.triggers_sent, 0)
            self.assertEqual(state.reason, "not_armed")

    def test_arm_resets_counter_and_remaining_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "arm_state.json"
            store = ArmStateStore(path)

            armed = store.arm(max_triggers=2)

            self.assertTrue(armed.enabled)
            self.assertEqual(armed.max_triggers, 2)
            self.assertEqual(armed.triggers_sent, 0)
            self.assertEqual(armed.remaining_triggers, 2)
            self.assertEqual(armed.reason, "armed")

    def test_record_success_auto_disarms_after_budget_exhausted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "arm_state.json"
            store = ArmStateStore(path)
            store.arm(max_triggers=1)

            after_send = store.record_success()

            self.assertFalse(after_send.enabled)
            self.assertEqual(after_send.triggers_sent, 1)
            self.assertEqual(after_send.remaining_triggers, 0)
            self.assertEqual(after_send.reason, "max_triggers_exhausted")

    def test_unlimited_mode_stays_armed_after_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "arm_state.json"
            store = ArmStateStore(path)
            store.arm(max_triggers=None)

            after_send = store.record_success()

            self.assertTrue(after_send.enabled)
            self.assertIsNone(after_send.max_triggers)
            self.assertEqual(after_send.triggers_sent, 1)
            self.assertIsNone(after_send.remaining_triggers)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new test and verify it fails**

Run: `python -m unittest tests.test_arm_state_store -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'core.arm_state'`

- [ ] **Step 3: Implement the armed-state model and store**

Create `core/arm_state.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ArmState:
    enabled: bool = False
    mode: str = "armed_current_chat"
    max_triggers: int | None = None
    triggers_sent: int = 0
    reason: str = "not_armed"

    @property
    def remaining_triggers(self) -> int | None:
        if self.max_triggers is None:
            return None
        return max(self.max_triggers - self.triggers_sent, 0)

    def to_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "max_triggers": self.max_triggers,
            "triggers_sent": self.triggers_sent,
            "remaining_triggers": self.remaining_triggers,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ArmState":
        raw_max = payload.get("max_triggers")
        max_triggers = None if raw_max in (None, "", "unlimited") else int(raw_max)
        return cls(
            enabled=bool(payload.get("enabled", False)),
            mode=str(payload.get("mode") or "armed_current_chat"),
            max_triggers=max_triggers,
            triggers_sent=int(payload.get("triggers_sent") or 0),
            reason=str(payload.get("reason") or "not_armed"),
        )


class ArmStateStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path).resolve()

    def read(self) -> ArmState:
        if not self._path.exists():
            return ArmState()
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return ArmState()
        return ArmState.from_dict(payload)

    def arm(self, max_triggers: int | None) -> ArmState:
        state = ArmState(
            enabled=True,
            mode="armed_current_chat",
            max_triggers=max_triggers,
            triggers_sent=0,
            reason="armed",
        )
        self._write(state)
        return state

    def disarm(self, reason: str = "manual_disarm") -> ArmState:
        current = self.read()
        state = ArmState(
            enabled=False,
            mode=current.mode,
            max_triggers=current.max_triggers,
            triggers_sent=current.triggers_sent,
            reason=reason,
        )
        self._write(state)
        return state

    def record_success(self) -> ArmState:
        current = self.read()
        sent = current.triggers_sent + 1
        exhausted = current.max_triggers is not None and sent >= current.max_triggers
        state = ArmState(
            enabled=not exhausted,
            mode=current.mode,
            max_triggers=current.max_triggers,
            triggers_sent=sent,
            reason="max_triggers_exhausted" if exhausted else "armed",
        )
        self._write(state)
        return state

    def _write(self, state: ArmState) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
```

Modify `core/models.py` inside `RuntimeConfig`:

```python
@dataclass(slots=True)
class RuntimeConfig:
    watcher_backend: str = "replay"
    watcher_url: str = "http://127.0.0.1:5678"
    poll_interval_ms: int = 300
    history_limit: int = 200
    sender_backend: str = "dry_run"
    dry_run: bool = True
    inter_message_delay_ms: int = 180
    retry_count: int = 1
    log_dir: str = "logs"
    arm_state_path: str = "config/arm_state.local.json"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RuntimeConfig":
        return cls(
            watcher_backend=str(payload.get("watcher_backend") or "replay"),
            watcher_url=str(payload.get("watcher_url") or "http://127.0.0.1:5678"),
            poll_interval_ms=int(payload.get("poll_interval_ms") or 300),
            history_limit=int(payload.get("history_limit") or 200),
            sender_backend=str(payload.get("sender_backend") or "dry_run"),
            dry_run=bool(payload.get("dry_run", True)),
            inter_message_delay_ms=int(payload.get("inter_message_delay_ms") or 180),
            retry_count=int(payload.get("retry_count") or 1),
            log_dir=str(payload.get("log_dir") or "logs"),
            arm_state_path=str(payload.get("arm_state_path") or "config/arm_state.local.json"),
        )
```

- [ ] **Step 4: Add the example and local arm-state files plus runtime wiring**

Create `config/arm_state.example.json` and `config/arm_state.local.json`:

```json
{
  "enabled": false,
  "mode": "armed_current_chat",
  "max_triggers": 1,
  "triggers_sent": 0,
  "remaining_triggers": 1,
  "reason": "not_armed"
}
```

Update `config/runtime.example.json` and `config/runtime.local.json`:

```json
{
  "watcher_backend": "replay",
  "watcher_url": "http://127.0.0.1:5678",
  "poll_interval_ms": 300,
  "history_limit": 200,
  "sender_backend": "dry_run",
  "dry_run": true,
  "inter_message_delay_ms": 180,
  "retry_count": 1,
  "log_dir": "logs",
  "arm_state_path": "config/arm_state.local.json"
}
```

- [ ] **Step 5: Run the armed-state test and verify it passes**

Run: `python -m unittest tests.test_arm_state_store -v`

Expected: PASS with 4 passing tests

- [ ] **Step 6: Commit the state-plumbing stage**

```bash
git add core/arm_state.py core/models.py config/arm_state.example.json config/arm_state.local.json config/runtime.example.json config/runtime.local.json tests/test_arm_state_store.py
git commit -m "feat(glacier): add armed current-chat state store"
```

### Task 2: Gate The Bot With Armed State And Trigger Budget

**Files:**
- Create: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\tests\test_bot_armed_current_chat.py`
- Modify: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\core\bot.py`
- Modify: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\core\dispatcher.py`
- Modify: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\scripts\run_bot.py`
- Test: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\tests\test_bot_armed_current_chat.py`

- [ ] **Step 1: Write the failing bot gating tests**

```python
from __future__ import annotations

import logging
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.arm_state import ArmStateStore
from core.bot import WeChatAutomationBot
from core.dispatcher import SendDispatcher
from core.models import MessageEvent, MessageType, Rule, RuntimeConfig


class MemorySender:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def send_text(self, context: MessageEvent, message: str) -> None:
        self.sent.append(message)


def build_event(seq: str) -> MessageEvent:
    return MessageEvent(
        seq=seq,
        timestamp="1",
        talker="filehelper",
        talker_name="文件传输助手",
        is_chat_room=False,
        sender="",
        sender_name="",
        message_type=MessageType.TEXT,
        content="START",
    )


def build_rule() -> Rule:
    return Rule.from_dict(
        {
            "id": "filehelper_start_sequence",
            "enabled": True,
            "talker": "文件传输助手",
            "sender": "",
            "chat_scope": "private",
            "type": "text",
            "match_mode": "exact",
            "pattern": "START",
            "cooldown_ms": 0,
            "replies": ["TEST", "第二条"],
        }
    )


class ArmedBotTest(unittest.TestCase):
    def test_disarmed_state_blocks_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ArmStateStore(Path(tmp) / "arm_state.json")
            sender = MemorySender()
            dispatcher = SendDispatcher(sender, RuntimeConfig(), logging.getLogger("test"))
            bot = WeChatAutomationBot([build_rule()], dispatcher, logging.getLogger("test"), store)

            bot.process(build_event("evt-1"))

            self.assertEqual(sender.sent, [])

    def test_successful_batch_consumes_budget_and_auto_disarms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ArmStateStore(Path(tmp) / "arm_state.json")
            store.arm(max_triggers=1)
            sender = MemorySender()
            dispatcher = SendDispatcher(sender, RuntimeConfig(), logging.getLogger("test"))
            bot = WeChatAutomationBot([build_rule()], dispatcher, logging.getLogger("test"), store)

            bot.process(build_event("evt-1"))
            bot.process(build_event("evt-2"))

            self.assertEqual(sender.sent, ["TEST", "第二条"])
            self.assertFalse(store.read().enabled)
            self.assertEqual(store.read().reason, "max_triggers_exhausted")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the bot-gating test and verify it fails**

Run: `python -m unittest tests.test_bot_armed_current_chat -v`

Expected: FAIL because `WeChatAutomationBot.__init__()` does not accept an arm-state store yet

- [ ] **Step 3: Return a dispatch result and wire arm-state checks into the bot**

Modify `core/dispatcher.py`:

```python
from dataclasses import dataclass


@dataclass(slots=True)
class DispatchReport:
    attempted: int
    sent: int


class SendDispatcher:
    def dispatch(self, rule: Rule, context: MessageEvent) -> DispatchReport:
        sent = 0
        for index, reply in enumerate(rule.replies, start=1):
            self._send_with_retry(context, reply, rule.id, index)
            sent += 1
            if index != len(rule.replies):
                time.sleep(self._runtime.inter_message_delay_ms / 1000.0)
        return DispatchReport(attempted=len(rule.replies), sent=sent)
```

Modify `core/bot.py`:

```python
from .arm_state import ArmStateStore


class WeChatAutomationBot:
    def __init__(
        self,
        rules: list[Rule],
        dispatcher: SendDispatcher,
        logger: logging.Logger,
        arm_state_store: ArmStateStore,
    ) -> None:
        self._rules = rules
        self._dispatcher = dispatcher
        self._logger = logger
        self._arm_state_store = arm_state_store
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
            report = self._dispatcher.dispatch(rule, event)
            if report.sent == len(rule.replies):
                updated = self._arm_state_store.record_success()
                self._logger.info(
                    "armed_state_update enabled=%s sent=%s remaining=%s reason=%s",
                    updated.enabled,
                    updated.triggers_sent,
                    updated.remaining_triggers,
                    updated.reason,
                )
```

Modify `scripts/run_bot.py`:

```python
from core.arm_state import ArmStateStore


def main() -> int:
    args = parse_args()
    runtime = load_runtime_config(args.runtime)
    rules = load_rules(args.rules)

    log_dir = (ROOT / runtime.log_dir).resolve()
    logger = configure_logger("wechat_automation", log_dir)
    sender = create_sender(runtime, logger)
    dispatcher = SendDispatcher(sender, runtime, logger)
    arm_state_store = ArmStateStore(ROOT / runtime.arm_state_path)
    bot = WeChatAutomationBot(rules, dispatcher, logger, arm_state_store)
```

- [ ] **Step 4: Run the new gating tests and the existing matcher tests**

Run: `python -m unittest tests.test_bot_armed_current_chat tests.test_matcher_chat_scope tests.test_live_filehelper_normalization -v`

Expected: PASS with the new armed-state behavior and the existing rule matching still green

- [ ] **Step 5: Commit the bot-gating stage**

```bash
git add core/bot.py core/dispatcher.py scripts/run_bot.py tests/test_bot_armed_current_chat.py
git commit -m "feat(glacier): gate bot with armed trigger budget"
```

### Task 3: Implement Lightweight Current-Chat Sending

**Files:**
- Create: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\core\current_chat_sender.py`
- Create: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\tests\test_current_chat_sender.py`
- Create: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\scripts\current_chat_probe.py`
- Modify: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\core\sender_adapter.py`
- Test: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\tests\test_current_chat_sender.py`

- [ ] **Step 1: Write the failing current-chat sender tests**

```python
from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.current_chat_sender import CurrentChatSender, WindowSnapshot
from core.models import MessageEvent, MessageType


class DummyWindowInspector:
    def __init__(self, snapshot: WindowSnapshot) -> None:
        self._snapshot = snapshot

    def snapshot(self) -> WindowSnapshot:
        return self._snapshot


class DummyFocusProvider:
    def __init__(self, control: object) -> None:
        self._control = control

    def get_focused_control(self) -> object:
        return self._control


class DummyInputDriver:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def send_text(self, control: object, text: str) -> bool:
        self.sent.append(text)
        return True


class DummyControl:
    ControlTypeName = "EditControl"


def build_event() -> MessageEvent:
    return MessageEvent(
        seq="evt",
        timestamp="1",
        talker="filehelper",
        talker_name="文件传输助手",
        is_chat_room=False,
        sender="",
        sender_name="",
        message_type=MessageType.TEXT,
        content="START",
    )


class CurrentChatSenderTest(unittest.TestCase):
    def test_rejects_non_wechat_foreground_window(self) -> None:
        sender = CurrentChatSender(
            logger=logging.getLogger("test"),
            window_inspector=DummyWindowInspector(
                WindowSnapshot(hwnd=1, title="记事本", class_name="Notepad")
            ),
            focus_provider=DummyFocusProvider(DummyControl()),
            input_driver=DummyInputDriver(),
        )

        with self.assertRaisesRegex(RuntimeError, "foreground_not_wechat"):
            sender.send_text(build_event(), "TEST")

    def test_sends_when_wechat_window_and_edit_focus_are_ready(self) -> None:
        driver = DummyInputDriver()
        sender = CurrentChatSender(
            logger=logging.getLogger("test"),
            window_inspector=DummyWindowInspector(
                WindowSnapshot(hwnd=1, title="微信", class_name="WeChatMainWndForPC")
            ),
            focus_provider=DummyFocusProvider(DummyControl()),
            input_driver=driver,
        )

        sender.send_text(build_event(), "TEST")

        self.assertEqual(driver.sent, ["TEST"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new sender test and verify it fails**

Run: `python -m unittest tests.test_current_chat_sender -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'core.current_chat_sender'`

- [ ] **Step 3: Implement the foreground guard and current-chat sender**

Create `core/current_chat_sender.py`:

```python
from __future__ import annotations

import ctypes
import logging
from dataclasses import dataclass
from typing import Protocol

from .models import MessageEvent


@dataclass(slots=True)
class WindowSnapshot:
    hwnd: int
    title: str
    class_name: str

    @property
    def looks_like_wechat(self) -> bool:
        title = self.title or ""
        class_name = self.class_name or ""
        return "微信" in title or "WeChat" in class_name


class WindowInspector(Protocol):
    def snapshot(self) -> WindowSnapshot:
        ...


class FocusProvider(Protocol):
    def get_focused_control(self) -> object:
        ...


class InputDriver(Protocol):
    def send_text(self, control: object, text: str) -> bool:
        ...


class Win32WindowInspector:
    def snapshot(self) -> WindowSnapshot:
        user32 = ctypes.windll.user32
        hwnd = int(user32.GetForegroundWindow())
        title_buffer = ctypes.create_unicode_buffer(512)
        class_buffer = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title_buffer, len(title_buffer))
        user32.GetClassNameW(hwnd, class_buffer, len(class_buffer))
        return WindowSnapshot(hwnd=hwnd, title=title_buffer.value, class_name=class_buffer.value)


class Wx4pyFocusProvider:
    def get_focused_control(self) -> object:
        from wx4py.core import uiautomation as auto

        return auto.GetFocusedControl()


class Wx4pyInputDriver:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def send_text(self, control: object, text: str) -> bool:
        from wx4py.features.chat import ChatWindow

        return ChatWindow.send_text_via_input(control, text, logger_override=self._logger)


class CurrentChatSender:
    def __init__(
        self,
        logger: logging.Logger,
        window_inspector: WindowInspector | None = None,
        focus_provider: FocusProvider | None = None,
        input_driver: InputDriver | None = None,
    ) -> None:
        self._logger = logger
        self._window_inspector = window_inspector or Win32WindowInspector()
        self._focus_provider = focus_provider or Wx4pyFocusProvider()
        self._input_driver = input_driver or Wx4pyInputDriver(logger)

    def send_text(self, context: MessageEvent, message: str) -> None:
        window = self._window_inspector.snapshot()
        if not window.looks_like_wechat:
            raise RuntimeError("foreground_not_wechat")

        control = self._focus_provider.get_focused_control()
        control_type = str(getattr(control, "ControlTypeName", "") or "")
        if control_type not in {"EditControl", "DocumentControl"}:
            raise RuntimeError("focused_control_not_editable")

        if not self._input_driver.send_text(control, message):
            raise RuntimeError("current_chat_send_failed")

        self._logger.info(
            "current_chat_send talker=%s sender=%s payload=%s",
            context.display_talker,
            context.display_sender,
            message,
        )
```

Modify `core/sender_adapter.py`:

```python
from .current_chat_sender import CurrentChatSender


class Wx4pySender:
    def send_text(self, context: MessageEvent, message: str) -> None:
        target_name = context.display_talker
        target_type = "group" if context.is_chat_room else "contact"
        with self._client_cls(auto_connect=True) as wx:
            sent = wx.chat_window.send_to(target_name, message, target_type=target_type)
        if not sent:
            raise RuntimeError(f"wx4py_send_failed target={target_name}")
        self._logger.info(
            "wx4py_send talker=%s target_type=%s payload=%s",
            target_name,
            target_type,
            message,
        )


def create_sender(runtime: RuntimeConfig, logger: logging.Logger) -> Sender:
    backend = runtime.sender_backend.lower().strip()
    if runtime.dry_run or backend == "dry_run":
        return DryRunSender(logger)
    if backend == "current_chat":
        return CurrentChatSender(logger)
    if backend == "wx4py":
        return Wx4pySender(logger)
    raise ValueError(f"Unsupported sender backend: {runtime.sender_backend}")
```

Create `scripts/current_chat_probe.py`:

```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config_loader import load_runtime_config
from core.logger import configure_logger
from core.models import MessageEvent, MessageType
from core.sender_adapter import create_sender


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send one message into the current WeChat chat.")
    parser.add_argument("--runtime", required=True, help="Path to runtime config JSON/YAML.")
    parser.add_argument("--message", required=True, help="Message to send into the current chat.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime = load_runtime_config(args.runtime)
    logger = configure_logger("wechat_automation_probe", (ROOT / runtime.log_dir).resolve())
    sender = create_sender(runtime, logger)
    probe_event = MessageEvent(
        seq="probe",
        timestamp="0",
        talker="current_chat",
        talker_name="当前聊天",
        is_chat_room=False,
        sender="",
        sender_name="",
        message_type=MessageType.TEXT,
        content="",
    )
    sender.send_text(probe_event, args.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the sender tests**

Run: `python -m unittest tests.test_current_chat_sender -v`

Expected: PASS with one blocked-non-WeChat case and one success case

- [ ] **Step 5: Commit the lightweight sender stage**

```bash
git add core/current_chat_sender.py core/sender_adapter.py scripts/current_chat_probe.py tests/test_current_chat_sender.py
git commit -m "feat(glacier): add current chat sender"
```

### Task 4: Add Manual Arm/Disarm Controls To The Web Console

**Files:**
- Modify: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\scripts\web_console.py`
- Modify: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\web\index.html`
- Modify: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\web\app.js`
- Modify: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\tests\test_web_console_api.py`
- Test: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\tests\test_web_console_api.py`

- [ ] **Step 1: Extend the web-console API test first**

Add this test into `tests/test_web_console_api.py`:

```python
    def test_arm_state_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_path = Path(tmp) / "runtime.json"
            rules_path = Path(tmp) / "rules.json"
            arm_state_path = Path(tmp) / "arm_state.json"
            runtime_path.write_text(
                json.dumps(
                    {
                        "watcher_url": "http://127.0.0.1:5678",
                        "sender_backend": "dry_run",
                        "dry_run": True,
                        "arm_state_path": str(arm_state_path),
                    }
                ),
                encoding="utf-8",
            )
            rules_path.write_text("[]", encoding="utf-8")
            arm_state_path.write_text(
                json.dumps(
                    {
                        "enabled": False,
                        "mode": "armed_current_chat",
                        "max_triggers": 1,
                        "triggers_sent": 0,
                        "remaining_triggers": 1,
                        "reason": "not_armed",
                    }
                ),
                encoding="utf-8",
            )

            app = create_app(runtime_path=runtime_path, rules_path=rules_path, watcher_factory=DummyWatcher)
            client = app.test_client()

            get_state = client.get("/api/arm-state")
            self.assertEqual(get_state.status_code, 200)
            self.assertFalse(get_state.get_json()["enabled"])

            arm_response = client.post("/api/arm-state", json={"enabled": True, "max_triggers": 2})
            self.assertEqual(arm_response.status_code, 200)
            self.assertTrue(arm_response.get_json()["enabled"])
            self.assertEqual(arm_response.get_json()["remaining_triggers"], 2)

            disarm_response = client.post("/api/arm-state", json={"enabled": False})
            self.assertEqual(disarm_response.status_code, 200)
            self.assertFalse(disarm_response.get_json()["enabled"])
            self.assertEqual(disarm_response.get_json()["reason"], "manual_disarm")
```

- [ ] **Step 2: Run the web-console API test and verify it fails**

Run: `python -m unittest tests.test_web_console_api -v`

Expected: FAIL because `/api/arm-state` does not exist yet

- [ ] **Step 3: Add arm-state endpoints and a small control panel**

Modify `scripts/web_console.py`:

```python
from core.arm_state import ArmStateStore


def create_app(
    runtime_path: str | Path,
    rules_path: str | Path,
    watcher_factory: Callable[[RuntimeConfig], object] | None = None,
) -> Flask:
    app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="/web")
    resolved_runtime_path = Path(runtime_path).resolve()
    resolved_rules_path = Path(rules_path).resolve()

    def build_arm_state_store() -> ArmStateStore:
        runtime = load_runtime_config(resolved_runtime_path)
        return ArmStateStore(ROOT / runtime.arm_state_path)

    @app.get("/api/arm-state")
    def get_arm_state() -> object:
        store = build_arm_state_store()
        return jsonify(store.read().to_dict())

    @app.post("/api/arm-state")
    def save_arm_state() -> object:
        payload = request.get_json(force=True)
        if not isinstance(payload, dict):
            return jsonify({"ok": False, "error": "arm-state payload must be an object"}), 400

        store = build_arm_state_store()
        enabled = bool(payload.get("enabled", False))
        if enabled:
            raw_max = payload.get("max_triggers")
            max_triggers = None if raw_max in (None, "", "unlimited") else int(raw_max)
            state = store.arm(max_triggers=max_triggers)
        else:
            state = store.disarm(reason="manual_disarm")
        return jsonify(state.to_dict())
```

Add this section to `web/index.html` above the rule form:

```html
<section>
  <div class="section-title">
    <h2>实验控制</h2>
  </div>
  <div class="field">
    <label for="max-triggers">触发上限</label>
    <input id="max-triggers" type="text" value="1" />
  </div>
  <div class="actions">
    <button id="arm-once" type="button">启动监听</button>
    <button id="arm-unlimited" class="secondary" type="button">无上限启动</button>
    <button id="disarm" class="secondary" type="button">停止监听</button>
  </div>
  <div class="note" id="arm-status">当前未启动。</div>
</section>
```

Modify `web/app.js`:

```javascript
const armStatusNode = document.getElementById('arm-status');
const armOnceButton = document.getElementById('arm-once');
const armUnlimitedButton = document.getElementById('arm-unlimited');
const disarmButton = document.getElementById('disarm');
const maxTriggersInput = document.getElementById('max-triggers');

function renderArmState(state) {
  if (!armStatusNode) {
    return;
  }
  const remaining = state.remaining_triggers == null ? '无限' : String(state.remaining_triggers);
  armStatusNode.textContent = state.enabled
    ? `当前已启动，已触发 ${state.triggers_sent} 次，剩余 ${remaining} 次。`
    : `当前未启动，原因：${state.reason || 'not_armed'}。`;
}

async function loadArmState() {
  const response = await fetch('/api/arm-state');
  if (!response.ok) {
    throw new Error(`arm-state ${response.status}`);
  }
  renderArmState(await response.json());
}

async function updateArmState(payload) {
  armStatusNode.textContent = '正在更新实验状态...';
  const response = await fetch('/api/arm-state', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`arm-state-save ${response.status}`);
  }
  renderArmState(await response.json());
}

armOnceButton.addEventListener('click', () => {
  const value = String(maxTriggersInput.value || '1').trim();
  updateArmState({ enabled: true, max_triggers: Number(value || '1') });
});

armUnlimitedButton.addEventListener('click', () => {
  updateArmState({ enabled: true, max_triggers: 'unlimited' });
});

disarmButton.addEventListener('click', () => {
  updateArmState({ enabled: false });
});

loadArmState();
window.setInterval(loadArmState, 3000);
```

- [ ] **Step 4: Run the web-console test again**

Run: `python -m unittest tests.test_web_console_api -v`

Expected: PASS with both the existing rules/events checks and the new arm-state round trip

- [ ] **Step 5: Commit the control-console stage**

```bash
git add scripts/web_console.py web/index.html web/app.js tests/test_web_console_api.py
git commit -m "feat(glacier): add arm controls to web console"
```

### Task 5: Verification, Docs, And User-Gated Manual Send

**Files:**
- Modify: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\README.md`
- Modify: `D:\flutter_app\super_ivan_pro\docs\progress\wechat_automation_current_status_2026-04-21.md`
- Test: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\tests\test_arm_state_store.py`
- Test: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\tests\test_bot_armed_current_chat.py`
- Test: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\tests\test_current_chat_sender.py`
- Test: `D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\tests\test_web_console_api.py`

- [ ] **Step 1: Update the README to document the new run mode**

Add this section to `README.md`:

```markdown
## Armed current-chat mode

This mode is optimized for fastest local response:

- the operator manually opens the target chat first
- the operator manually arms the experiment from the local web console
- the bot keeps listening through `wechat-decrypt`
- when the trigger matches, replies are sent into the current WeChat chat only
- the run auto-disarms after the configured trigger budget is exhausted

Important safety boundary:

- this mode must not send unless the foreground window is WeChat
- this mode must not send unless the focused control is editable
- any real send still requires explicit user approval before the manual probe step
```

- [ ] **Step 2: Update the continuity doc with the implementation result**

Add this summary block to `docs/progress/wechat_automation_current_status_2026-04-21.md`:

```markdown
## Armed current-chat stage result

- added file-backed arm/disarm state under `config/arm_state.local.json`
- added `current_chat` sender backend for foreground-WeChat sending
- added trigger budget exhaustion and auto-disarm
- added web-console arm/disarm controls and remaining-budget display
- kept named-target `wx4py` sending as a separate later-stage capability
```

- [ ] **Step 3: Run the full Python test suite**

Run: `python -m unittest discover tests -v`

Expected: PASS across matcher, live watcher, arm state, bot gating, current-chat sender, and web console API tests

- [ ] **Step 4: Run the safe local console smoke test**

Run: `python scripts/web_console.py --runtime config/runtime.local.json --rules config/rules.local.json --host 127.0.0.1 --port 8090`

Expected: local Flask server starts and `http://127.0.0.1:8090` shows:

- 实验控制
- 最近事件
- 规则编辑

- [ ] **Step 5: Ask the user before any real send, then run one manual current-chat probe**

Run only after explicit user approval:

`python scripts/current_chat_probe.py --runtime config/runtime.local.json --message "test"`

Expected:

- foreground WeChat chat receives exactly one `test`
- if another app is frontmost, the probe fails with `foreground_not_wechat`
- no named-target search is performed

- [ ] **Step 6: Commit the documentation and verification stage**

```bash
git add README.md docs/progress/wechat_automation_current_status_2026-04-21.md
git commit -m "docs(glacier): document armed current-chat mode"
```
