# WeChat Automation Web Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local web console that shows recent live WeChat events, lets the operator pick a listener target from those events, edits one local rule set, and saves the rule file without touching real message sending.

**Architecture:** Add a small Flask app inside the standalone `glacier/wechat_automation` module. The app will reuse the existing runtime/rule loaders and the live watcher normalization logic, expose JSON endpoints for recent events and rule persistence, and serve one lightweight HTML page with plain JavaScript for operator control.

**Tech Stack:** Python 3.10, Flask, existing `wechat_automation` core modules, plain HTML/CSS/JavaScript, `unittest`

---

## File Structure

- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_matcher_chat_scope.py`
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_web_console_api.py`
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/scripts/web_console.py`
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/web/index.html`
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/web/app.js`
- Modify: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/core/models.py`
- Modify: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/core/matcher.py`
- Modify: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/core/watcher_adapter.py`
- Modify: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/README.md`
- Modify: `docs/progress/wechat_automation_current_status_2026-04-21.md`

### Task 1: Add Explicit Chat Scope Support

**Files:**
- Test: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_matcher_chat_scope.py`
- Modify: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/core/models.py`
- Modify: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/core/matcher.py`

- [ ] **Step 1: Write the failing test**

```python
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.matcher import match_rule
from core.models import MessageEvent, MessageType, Rule


class MatcherChatScopeTest(unittest.TestCase):
    def test_private_scope_accepts_private_event(self) -> None:
        rule = Rule.from_dict(
            {
                "id": "private_only",
                "enabled": True,
                "talker": "文件传输助手",
                "sender": "",
                "type": "text",
                "chat_scope": "private",
                "match_mode": "exact",
                "pattern": "START",
                "cooldown_ms": 0,
                "replies": ["OK"],
            }
        )
        message = MessageEvent(
            seq="1",
            timestamp="1",
            talker="filehelper",
            talker_name="文件传输助手",
            is_chat_room=False,
            sender="",
            sender_name="",
            message_type=MessageType.TEXT,
            content="START",
        )

        result = match_rule(message, rule)
        self.assertTrue(result.matched)

    def test_private_scope_rejects_group_event(self) -> None:
        rule = Rule.from_dict(
            {
                "id": "private_only",
                "enabled": True,
                "talker": "测试群",
                "sender": "",
                "type": "text",
                "chat_scope": "private",
                "match_mode": "exact",
                "pattern": "START",
                "cooldown_ms": 0,
                "replies": ["OK"],
            }
        )
        message = MessageEvent(
            seq="2",
            timestamp="2",
            talker="123@chatroom",
            talker_name="测试群",
            is_chat_room=True,
            sender="Alice",
            sender_name="Alice",
            message_type=MessageType.TEXT,
            content="START",
        )

        result = match_rule(message, rule)
        self.assertFalse(result.matched)
        self.assertEqual(result.reason, "chat_scope_mismatch")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.tests.test_matcher_chat_scope`

Expected: FAIL because `Rule` does not yet support `chat_scope` and the matcher does not filter on group/private scope.

- [ ] **Step 3: Write minimal implementation**

```python
class ChatScope(str, Enum):
    ANY = "any"
    GROUP = "group"
    PRIVATE = "private"


@dataclass(slots=True)
class Rule:
    ...
    chat_scope: ChatScope
    ...

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Rule":
        return cls(
            ...
            chat_scope=ChatScope(str(payload.get("chat_scope") or "any").lower()),
            ...
        )


def _matches_chat_scope(message: MessageEvent, rule: Rule) -> bool:
    if rule.chat_scope == ChatScope.ANY:
        return True
    if rule.chat_scope == ChatScope.GROUP:
        return message.is_chat_room
    if rule.chat_scope == ChatScope.PRIVATE:
        return not message.is_chat_room
    return False


def match_rule(message: MessageEvent, rule: Rule) -> MatchResult:
    ...
    if not _matches_chat_scope(message, rule):
        return MatchResult(False, "chat_scope_mismatch")
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.tests.test_matcher_chat_scope`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_matcher_chat_scope.py android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/core/models.py android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/core/matcher.py
git commit -m "feat(glacier): add chat scope matching"
```

### Task 2: Expose Snapshot-Friendly Live Event Fetching

**Files:**
- Test: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_web_console_api.py`
- Modify: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/core/watcher_adapter.py`

- [ ] **Step 1: Write the failing test**

```python
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.models import RuntimeConfig
from core.watcher_adapter import WechatDecryptHistoryWatcher


class WebConsoleWatcherSnapshotTest(unittest.TestCase):
    def test_snapshot_normalizes_recent_payloads(self) -> None:
        watcher = WechatDecryptHistoryWatcher(RuntimeConfig())
        payloads = [
            {
                "timestamp": 1776787441,
                "chat": "filehelper",
                "username": "filehelper",
                "is_group": False,
                "sender": "",
                "type": "文本",
                "content": "START",
            }
        ]

        events = watcher.normalize_payloads(payloads)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].display_talker, "文件传输助手")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.tests.test_web_console_api.WebConsoleWatcherSnapshotTest`

Expected: FAIL because the watcher does not yet expose a snapshot normalization helper for the web console.

- [ ] **Step 3: Write minimal implementation**

```python
class WechatDecryptHistoryWatcher:
    ...
    def normalize_payloads(self, payloads: list[dict]) -> list[MessageEvent]:
        events: list[MessageEvent] = []
        for payload in payloads:
            event = self._normalize_payload(payload)
            if event:
                events.append(event)
        return events

    def fetch_recent_events(self, limit: int = 50, chat: str = "") -> list[MessageEvent]:
        params = {
            "since": "0",
            "limit": str(limit),
        }
        if chat:
            params["chat"] = chat
        payloads = self._fetch_history(params)
        return self.normalize_payloads(payloads)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.tests.test_web_console_api.WebConsoleWatcherSnapshotTest`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_web_console_api.py android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/core/watcher_adapter.py
git commit -m "feat(glacier): add watcher snapshot helpers"
```

### Task 3: Build the Local Web Console Backend

**Files:**
- Test: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_web_console_api.py`
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/scripts/web_console.py`

- [ ] **Step 1: Write the failing API test**

```python
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.web_console import create_app


class WebConsoleApiTest(unittest.TestCase):
    def test_rules_round_trip_and_recent_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_path = Path(tmp) / "runtime.json"
            rules_path = Path(tmp) / "rules.json"
            runtime_path.write_text(
                json.dumps(
                    {
                        "watcher_url": "http://127.0.0.1:5678",
                        "sender_backend": "dry_run",
                        "dry_run": True,
                    }
                ),
                encoding="utf-8",
            )
            rules_path.write_text("[]", encoding="utf-8")

            app = create_app(
                runtime_path=runtime_path,
                rules_path=rules_path,
                watcher_factory=lambda runtime: None,
            )
            client = app.test_client()

            response = client.get("/api/rules")
            self.assertEqual(response.status_code, 200)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.tests.test_web_console_api.WebConsoleApiTest`

Expected: FAIL because the web console backend does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from flask import Flask, jsonify, request, send_from_directory


def create_app(runtime_path: Path, rules_path: Path, watcher_factory=None) -> Flask:
    app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="/web")

    @app.get("/")
    def index():
        return send_from_directory(WEB_DIR, "index.html")

    @app.get("/api/rules")
    def get_rules():
        payload = json.loads(rules_path.read_text(encoding="utf-8"))
        return jsonify(payload)

    @app.post("/api/rules")
    def save_rules():
        payload = request.get_json(force=True)
        rules_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return jsonify({"ok": True})

    @app.get("/api/events")
    def get_events():
        runtime = load_runtime_config(runtime_path)
        watcher = watcher_factory(runtime) if watcher_factory else WechatDecryptHistoryWatcher(runtime)
        events = watcher.fetch_recent_events(limit=int(request.args.get("limit", "50")))
        return jsonify([event.raw | {
            "seq": event.seq,
            "talker": event.talker,
            "talker_name": event.display_talker,
            "sender": event.sender,
            "sender_name": event.display_sender,
            "is_chat_room": event.is_chat_room,
            "type": event.message_type.value,
            "content": event.content,
        } for event in events])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.tests.test_web_console_api.WebConsoleApiTest`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/scripts/web_console.py android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_web_console_api.py
git commit -m "feat(glacier): add web console backend"
```

### Task 4: Build the Browser UI and Operator Docs

**Files:**
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/web/index.html`
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/web/app.js`
- Modify: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/README.md`
- Modify: `docs/progress/wechat_automation_current_status_2026-04-21.md`

- [ ] **Step 1: Write the failing UI expectation as a manual check**

Manual check target:

- page loads locally
- recent event list is visible
- clicking one event fills talker, sender, scope, type, and pattern helpers
- saving writes `rules.local.json`

- [ ] **Step 2: Implement the minimal HTML shell**

```html
<main>
  <section id="events-panel"></section>
  <section id="rule-panel">
    <form id="rule-form">
      <input name="talker" />
      <select name="chat_scope">
        <option value="any">any</option>
        <option value="group">group</option>
        <option value="private">private</option>
      </select>
      <input name="sender" />
      <select name="type"></select>
      <select name="match_mode"></select>
      <input name="pattern" />
      <textarea name="replies"></textarea>
      <button type="submit">保存规则</button>
    </form>
  </section>
  <script src="/web/app.js"></script>
</main>
```

- [ ] **Step 3: Implement the minimal browser logic**

```javascript
async function loadEvents() {
  const response = await fetch('/api/events?limit=40');
  const events = await response.json();
  renderEvents(events);
}

function applyEventToForm(event) {
  form.talker.value = event.talker_name || event.talker;
  form.sender.value = event.sender_name || event.sender || '';
  form.chat_scope.value = event.is_chat_room ? 'group' : 'private';
  form.type.value = event.type;
  form.pattern.value = event.content || '';
}

async function saveRule(payload) {
  await fetch('/api/rules', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify([payload]),
  });
}
```

- [ ] **Step 4: Document how to run and verify**

Add to `README.md`:

```powershell
python scripts/web_console.py `
  --runtime config/runtime.local.json `
  --rules config/rules.local.json `
  --host 127.0.0.1 `
  --port 8090
```

Document manual verification:

1. open `http://127.0.0.1:8090`
2. wait for recent events
3. click one event
4. save the rule
5. inspect `config/rules.local.json`

- [ ] **Step 5: Run final verification**

Run:

```bash
python -m unittest android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.tests.test_matcher_chat_scope
python -m unittest android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.tests.test_web_console_api
python -m compileall android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation
```

Expected:

- all tests PASS
- compileall exits 0

- [ ] **Step 6: Commit**

```bash
git add android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/web android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/README.md docs/progress/wechat_automation_current_status_2026-04-21.md
git commit -m "feat(glacier): add web rule console"
```
