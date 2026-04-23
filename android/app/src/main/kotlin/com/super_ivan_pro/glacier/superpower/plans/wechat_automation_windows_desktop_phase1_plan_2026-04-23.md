# WeChat Automation Windows Desktop Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working Windows desktop console for the existing WeChat automation experiment so the operator can start or stop the local service, edit the active target and rule, switch normal or rapid mode, and inspect live status without manually juggling multiple scripts.

**Architecture:** Replace the broken Flutter template with a single-page Windows console backed by small Dart models and a desktop controller boundary. Add a new Python desktop service entrypoint inside the existing `wechat_automation` workspace that persists desktop runtime state in `%LOCALAPPDATA%`, exposes local JSON endpoints, and wraps the current automation core behind one service process that Flutter can launch and query.

**Tech Stack:** Flutter Windows, Dart widget tests, Python 3.10 stdlib HTTP server, existing `wechat_automation` core modules, JSON file persistence, Windows local process launching via `dart:io`.

---

## Scope Lock

This plan intentionally covers only the first desktop milestone:

1. Flutter Windows single-page console.
2. Unified Python desktop service skeleton.
3. One-click start or stop of the local service process from Flutter.
4. Active target, rule, arm state, and mode editing through the service API.
5. Recent status and event preview in the desktop UI.

Explicitly deferred to later plans:

1. Bundled Python executable packaging.
2. Bundled `wechat-decrypt` runtime assets.
3. Full child-process management for `wechat-decrypt` and the live bot loop.
4. Fancy UI polish beyond a clean functional operator console.

## Planned File Structure

- `pubspec.yaml`: add the minimal Flutter dependencies needed for the desktop shell.
- `lib/main.dart`: reduce to a clean Windows entrypoint.
- `lib/app/app.dart`: root app and top-level dependency wiring.
- `lib/app/theme.dart`: basic Windows desktop theme tokens.
- `lib/features/desktop_console/models/desktop_models.dart`: shared status, target, rule, mode, and event models.
- `lib/features/desktop_console/data/desktop_service.dart`: service contract used by the UI.
- `lib/features/desktop_console/data/fake_desktop_service.dart`: in-memory implementation for early widget tests.
- `lib/features/desktop_console/data/http_desktop_service.dart`: HTTP-backed implementation for the real local service.
- `lib/features/desktop_console/data/windows_service_launcher.dart`: start or stop the Python service process on Windows.
- `lib/features/desktop_console/controller/desktop_console_controller.dart`: bridge between widgets and service calls.
- `lib/features/desktop_console/presentation/desktop_console_page.dart`: single-page operator console.
- `lib/features/desktop_console/presentation/widgets/...`: focused UI sections for status, target, rule, mode, and logs.
- `test/app_bootstrap_test.dart`: shell smoke test.
- `test/desktop_console_controller_test.dart`: controller behavior tests.
- `test/desktop_console_page_test.dart`: widget interaction tests.
- `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/desktop_service/__init__.py`: desktop service package marker.
- `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/desktop_service/config_paths.py`: `%LOCALAPPDATA%` runtime path resolver with dev override support.
- `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/desktop_service/state_store.py`: desktop state persistence.
- `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/desktop_service/http_api.py`: JSON request handlers.
- `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/scripts/desktop_service.py`: local service entry script.
- `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_desktop_service_store.py`: store tests.
- `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_desktop_service_api.py`: HTTP API tests.
- `android/app/src/main/kotlin/com/super_ivan_pro/glacier/discussion_progress/wechat_automation_windows_desktop_progress_2026-04-23.md`: local continuity note for the new desktop stage.

### Task 1: Rebuild the Flutter desktop foundation

**Files:**
- Modify: `pubspec.yaml`
- Modify: `lib/main.dart`
- Create: `lib/app/app.dart`
- Create: `lib/app/theme.dart`
- Create: `lib/features/desktop_console/models/desktop_models.dart`
- Create: `lib/features/desktop_console/data/desktop_service.dart`
- Create: `test/app_bootstrap_test.dart`

- [ ] **Step 1: Write the failing bootstrap widget test**

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/app/app.dart';

void main() {
  testWidgets('boots the windows desktop console shell', (tester) async {
    await tester.pumpWidget(const SuperIvanDesktopApp());

    expect(find.text('微信自动化桌面端'), findsOneWidget);
    expect(find.text('服务状态'), findsOneWidget);
    expect(find.text('监听对象'), findsOneWidget);
    expect(find.text('规则配置'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run the test and verify RED**

Run: `flutter test test/app_bootstrap_test.dart`

Expected: FAIL because `SuperIvanDesktopApp` does not exist and the current scaffold does not render the required Chinese console headings.

- [ ] **Step 3: Write the minimal app foundation**

```dart
// lib/main.dart
import 'package:super_ivan_pro/app/app.dart';

void main() {
  runApp(const SuperIvanDesktopApp());
}
```

```dart
// lib/app/app.dart
import 'package:flutter/material.dart';
import 'package:super_ivan_pro/app/theme.dart';

class SuperIvanDesktopApp extends StatelessWidget {
  const SuperIvanDesktopApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '微信自动化桌面端',
      theme: buildDesktopTheme(),
      home: Scaffold(
        appBar: AppBar(title: const Text('微信自动化桌面端')),
        body: const Padding(
          padding: EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('服务状态'),
              SizedBox(height: 12),
              Text('监听对象'),
              SizedBox(height: 12),
              Text('规则配置'),
            ],
          ),
        ),
      ),
    );
  }
}
```

```dart
// lib/features/desktop_console/data/desktop_service.dart
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

abstract class DesktopService {
  Future<DesktopSnapshot> loadSnapshot();
}
```

```dart
// lib/features/desktop_console/models/desktop_models.dart
class DesktopSnapshot {
  const DesktopSnapshot({
    required this.serviceStatusLabel,
    required this.activeTargetLabel,
    required this.rulePattern,
  });

  final String serviceStatusLabel;
  final String activeTargetLabel;
  final String rulePattern;
}
```

- [ ] **Step 4: Run the test and verify GREEN**

Run: `flutter test test/app_bootstrap_test.dart`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pubspec.yaml lib/main.dart lib/app lib/features/desktop_console/models lib/features/desktop_console/data test/app_bootstrap_test.dart
git commit -m "feat(glacier): rebuild desktop flutter foundation"
```

### Task 2: Build the single-page operator console with editable local state

**Files:**
- Create: `lib/features/desktop_console/data/fake_desktop_service.dart`
- Create: `lib/features/desktop_console/controller/desktop_console_controller.dart`
- Create: `lib/features/desktop_console/presentation/desktop_console_page.dart`
- Create: `lib/features/desktop_console/presentation/widgets/status_panel.dart`
- Create: `lib/features/desktop_console/presentation/widgets/target_panel.dart`
- Create: `lib/features/desktop_console/presentation/widgets/rule_panel.dart`
- Create: `lib/features/desktop_console/presentation/widgets/mode_panel.dart`
- Create: `lib/features/desktop_console/presentation/widgets/events_panel.dart`
- Create: `test/desktop_console_controller_test.dart`
- Create: `test/desktop_console_page_test.dart`
- Modify: `lib/features/desktop_console/models/desktop_models.dart`

- [ ] **Step 1: Write the failing controller and widget tests**

```dart
// test/desktop_console_controller_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/controller/desktop_console_controller.dart';
import 'package:super_ivan_pro/features/desktop_console/data/fake_desktop_service.dart';

void main() {
  test('saves the edited target and mode through the service', () async {
    final service = FakeDesktopService.seed();
    final controller = DesktopConsoleController(service);

    await controller.initialize();
    await controller.saveTarget(
      displayName: '多姆斯利普🌙',
      talker: '多姆斯利普🌙',
      isGroup: true,
    );
    await controller.setMode(DesktopMode.rapid);

    expect(service.lastSavedTarget?.displayName, '多姆斯利普🌙');
    expect(service.lastSavedMode, DesktopMode.rapid);
  });
}
```

```dart
// test/desktop_console_page_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/data/fake_desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/desktop_console_page.dart';

void main() {
  testWidgets('renders editable target and rule fields', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: DesktopConsolePage(service: FakeDesktopService.seed()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('最近会话'), findsOneWidget);
    expect(find.text('手动输入监听对象'), findsOneWidget);
    expect(find.text('极速模式'), findsOneWidget);
    expect(find.text('armed'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run tests and verify RED**

Run: `flutter test test/desktop_console_controller_test.dart test/desktop_console_page_test.dart`

Expected: FAIL because the controller, fake service save methods, and page sections do not exist yet.

- [ ] **Step 3: Write the minimal controller and section widgets**

```dart
// lib/features/desktop_console/controller/desktop_console_controller.dart
import 'package:flutter/foundation.dart';
import 'package:super_ivan_pro/features/desktop_console/data/desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

class DesktopConsoleController extends ChangeNotifier {
  DesktopConsoleController(this._service);

  final DesktopService _service;
  DesktopSnapshot? snapshot;

  Future<void> initialize() async {
    snapshot = await _service.loadSnapshot();
    notifyListeners();
  }

  Future<void> saveTarget({
    required String displayName,
    required String talker,
    required bool isGroup,
  }) async {
    await _service.saveTarget(
      ActiveTarget(
        displayName: displayName,
        talker: talker,
        isGroup: isGroup,
      ),
    );
    await initialize();
  }

  Future<void> setMode(DesktopMode mode) async {
    await _service.saveMode(mode);
    await initialize();
  }
}
```

```dart
// lib/features/desktop_console/data/desktop_service.dart
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

abstract class DesktopService {
  Future<DesktopSnapshot> loadSnapshot();
  Future<void> saveTarget(ActiveTarget target);
  Future<void> saveMode(DesktopMode mode);
}
```

```dart
// lib/features/desktop_console/data/fake_desktop_service.dart
import 'package:super_ivan_pro/features/desktop_console/data/desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

class FakeDesktopService implements DesktopService {
  FakeDesktopService.seed()
      : _snapshot = DesktopSnapshot.seed(),
        lastSavedMode = DesktopMode.normal;

  DesktopSnapshot _snapshot;
  ActiveTarget? lastSavedTarget;
  DesktopMode lastSavedMode;

  @override
  Future<DesktopSnapshot> loadSnapshot() async => _snapshot;

  @override
  Future<void> saveTarget(ActiveTarget target) async {
    lastSavedTarget = target;
    _snapshot = _snapshot.copyWith(activeTarget: target);
  }

  @override
  Future<void> saveMode(DesktopMode mode) async {
    lastSavedMode = mode;
    _snapshot = _snapshot.copyWith(mode: mode);
  }
}
```

```dart
// lib/features/desktop_console/models/desktop_models.dart
enum DesktopMode { normal, rapid }

class ActiveTarget {
  const ActiveTarget({
    required this.displayName,
    required this.talker,
    required this.isGroup,
  });

  final String displayName;
  final String talker;
  final bool isGroup;
}

class DesktopSnapshot {
  const DesktopSnapshot({
    required this.serviceStatusLabel,
    required this.activeTarget,
    required this.mode,
    required this.rulePattern,
  });

  factory DesktopSnapshot.seed() {
    return const DesktopSnapshot(
      serviceStatusLabel: '未启动',
      activeTarget: ActiveTarget(
        displayName: '文件传输助手',
        talker: 'filehelper',
        isGroup: false,
      ),
      mode: DesktopMode.normal,
      rulePattern: 'START',
    );
  }

  final String serviceStatusLabel;
  final ActiveTarget activeTarget;
  final DesktopMode mode;
  final String rulePattern;

  DesktopSnapshot copyWith({
    String? serviceStatusLabel,
    ActiveTarget? activeTarget,
    DesktopMode? mode,
    String? rulePattern,
  }) {
    return DesktopSnapshot(
      serviceStatusLabel: serviceStatusLabel ?? this.serviceStatusLabel,
      activeTarget: activeTarget ?? this.activeTarget,
      mode: mode ?? this.mode,
      rulePattern: rulePattern ?? this.rulePattern,
    );
  }
}
```

```dart
// lib/features/desktop_console/presentation/desktop_console_page.dart
class DesktopConsolePage extends StatefulWidget {
  const DesktopConsolePage({super.key, required this.service});

  final DesktopService service;

  @override
  State<DesktopConsolePage> createState() => _DesktopConsolePageState();
}

class _DesktopConsolePageState extends State<DesktopConsolePage> {
  late final DesktopConsoleController controller;

  @override
  void initState() {
    super.initState();
    controller = DesktopConsoleController(widget.service)..initialize();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('微信自动化桌面端')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: const [
          StatusPanel(),
          SizedBox(height: 16),
          TargetPanel(),
          SizedBox(height: 16),
          RulePanel(),
          SizedBox(height: 16),
          ModePanel(),
          SizedBox(height: 16),
          EventsPanel(),
        ],
      ),
    );
  }
}
```

- [ ] **Step 4: Run tests and verify GREEN**

Run: `flutter test test/desktop_console_controller_test.dart test/desktop_console_page_test.dart`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/features/desktop_console test/desktop_console_controller_test.dart test/desktop_console_page_test.dart
git commit -m "feat(glacier): add desktop console ui shell"
```

### Task 3: Add the Python desktop service state store and JSON API

**Files:**
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/desktop_service/__init__.py`
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/desktop_service/config_paths.py`
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/desktop_service/state_store.py`
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/desktop_service/http_api.py`
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/scripts/desktop_service.py`
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_desktop_service_store.py`
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_desktop_service_api.py`

- [ ] **Step 1: Write the failing Python tests**

```python
# test_desktop_service_store.py
import tempfile
import unittest
from pathlib import Path

from android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.desktop_service.state_store import DesktopStateStore


class DesktopStateStoreTest(unittest.TestCase):
    def test_persists_active_target_and_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = DesktopStateStore(Path(tmp))
            state = store.load()

            state["active_target"]["display_name"] = "多姆斯利普🌙"
            state["mode"] = "rapid"
            store.save(state)

            reloaded = store.load()
            self.assertEqual(reloaded["active_target"]["display_name"], "多姆斯利普🌙")
            self.assertEqual(reloaded["mode"], "rapid")
```

```python
# test_desktop_service_api.py
import json
import tempfile
import unittest
from pathlib import Path

from android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.desktop_service.http_api import create_app


class DesktopServiceApiTest(unittest.TestCase):
    def test_status_and_target_update_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(runtime_root=Path(tmp))
            status = app.handle_json("GET", "/status")
            self.assertEqual(status["mode"], "normal")

            app.handle_json(
                "POST",
                "/targets/active",
                {
                    "talker": "filehelper",
                    "display_name": "文件传输助手",
                    "is_group": False,
                },
            )
            updated = app.handle_json("GET", "/status")
            self.assertEqual(updated["active_target"]["display_name"], "文件传输助手")
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `python -m unittest android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.tests.test_desktop_service_store android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.tests.test_desktop_service_api -v`

Expected: FAIL because the desktop service package and handlers do not exist yet.

- [ ] **Step 3: Write the minimal desktop service**

```python
# config_paths.py
from pathlib import Path
import os


def resolve_runtime_root(override: Path | None = None) -> Path:
    if override is not None:
        return override
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA is required on Windows desktop runtime")
    return Path(local_app_data) / "SuperIvanPro" / "wechat_automation"
```

```python
# state_store.py
import json
from pathlib import Path


class DesktopStateStore:
    def __init__(self, runtime_root: Path) -> None:
        self._runtime_root = runtime_root
        self._state_path = runtime_root / "config" / "desktop_state.json"

    def load(self) -> dict:
        if not self._state_path.exists():
            state = {
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
            self.save(state)
            return state
        return json.loads(self._state_path.read_text(encoding="utf-8"))

    def save(self, state: dict) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
```

```python
# http_api.py
from pathlib import Path

from .config_paths import resolve_runtime_root
from .state_store import DesktopStateStore


class DesktopServiceApp:
    def __init__(self, runtime_root: Path) -> None:
        self._store = DesktopStateStore(runtime_root)

    def handle_json(self, method: str, path: str, payload: dict | None = None) -> dict:
        state = self._store.load()
        if method == "GET" and path == "/status":
            return state
        if method == "POST" and path == "/targets/active":
            state["active_target"] = {
                "talker": payload["talker"],
                "display_name": payload["display_name"],
                "is_group": payload["is_group"],
            }
            self._store.save(state)
            return state
        raise ValueError(f"unsupported route: {method} {path}")


def create_app(runtime_root: Path | None = None) -> DesktopServiceApp:
    return DesktopServiceApp(resolve_runtime_root(runtime_root))
```

```python
# scripts/desktop_service.py
from android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.desktop_service.http_api import create_app


def main() -> None:
    app = create_app()
    app.handle_json("GET", "/status")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -m unittest android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.tests.test_desktop_service_store android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.tests.test_desktop_service_api -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/desktop_service android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/scripts/desktop_service.py android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_desktop_service_store.py android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_desktop_service_api.py
git commit -m "feat(glacier): add desktop service api skeleton"
```

### Task 4: Wire Flutter to the live local service and Windows process control

**Files:**
- Create: `lib/features/desktop_console/data/http_desktop_service.dart`
- Create: `lib/features/desktop_console/data/windows_service_launcher.dart`
- Modify: `lib/features/desktop_console/data/desktop_service.dart`
- Modify: `lib/features/desktop_console/controller/desktop_console_controller.dart`
- Modify: `lib/features/desktop_console/presentation/desktop_console_page.dart`
- Create: `test/windows_service_launcher_test.dart`
- Create: `test/desktop_console_live_service_test.dart`

- [ ] **Step 1: Write the failing launcher and live-service tests**

```dart
// test/windows_service_launcher_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/data/fake_desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/data/windows_service_launcher.dart';

void main() {
  test('builds the python desktop service command with the expected workspace script', () {
    final launcher = WindowsServiceLauncher(
      workspaceRoot: r'D:\flutter_app\super_ivan_pro',
      pythonExecutable: 'python',
    );

    final command = launcher.buildStartCommand();
    expect(command.executable, 'python');
    expect(command.arguments.last, contains('scripts/desktop_service.py'));
  });
}
```

```dart
// test/desktop_console_live_service_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/controller/desktop_console_controller.dart';
import 'package:super_ivan_pro/features/desktop_console/data/fake_desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

class StubDesktopService extends FakeDesktopService {
  bool started = false;

  @override
  Future<void> startServices() async {
    started = true;
  }
}

void main() {
  test('start services updates controller busy state', () async {
    final service = StubDesktopService();
    final controller = DesktopConsoleController(service);

    await controller.startServices();

    expect(service.started, isTrue);
    expect(controller.isBusy, isFalse);
  });
}
```

- [ ] **Step 2: Run tests and verify RED**

Run: `flutter test test/windows_service_launcher_test.dart test/desktop_console_live_service_test.dart`

Expected: FAIL because the launcher command model and live service methods do not exist yet.

- [ ] **Step 3: Write the minimal live integration**

```dart
// http_desktop_service.dart
import 'dart:convert';
import 'dart:io';

import 'package:super_ivan_pro/features/desktop_console/data/desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

class HttpDesktopService implements DesktopService {
  HttpDesktopService(this._baseUri, {HttpClient? client})
      : _client = client ?? HttpClient();

  final Uri _baseUri;
  final HttpClient _client;

  @override
  Future<DesktopSnapshot> loadSnapshot() async {
    final request = await _client.getUrl(_baseUri.resolve('/status'));
    final response = await request.close();
    final payload = jsonDecode(await response.transform(utf8.decoder).join()) as Map<String, dynamic>;
    return DesktopSnapshot.fromJson(payload);
  }

  @override
  Future<void> saveTarget(ActiveTarget target) async {}

  @override
  Future<void> saveMode(DesktopMode mode) async {}

  @override
  Future<void> startServices() async {}
}
```

```dart
// windows_service_launcher.dart
class LaunchCommand {
  const LaunchCommand({required this.executable, required this.arguments});

  final String executable;
  final List<String> arguments;
}

class WindowsServiceLauncher {
  WindowsServiceLauncher({
    required this.workspaceRoot,
    required this.pythonExecutable,
  });

  final String workspaceRoot;
  final String pythonExecutable;

  LaunchCommand buildStartCommand() {
    return LaunchCommand(
      executable: pythonExecutable,
      arguments: [
        '$workspaceRoot/android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/scripts/desktop_service.py',
      ],
    );
  }
}
```

```dart
// desktop_service.dart additions
abstract class DesktopService {
  Future<DesktopSnapshot> loadSnapshot();
  Future<void> saveTarget(ActiveTarget target);
  Future<void> saveMode(DesktopMode mode);
  Future<void> startServices();
}
```

```dart
// desktop_models.dart additions
factory DesktopSnapshot.fromJson(Map<String, dynamic> json) {
  return DesktopSnapshot(
    serviceStatusLabel: json['service_state'] as String? ?? 'unknown',
    activeTarget: ActiveTarget(
      displayName: (json['active_target'] as Map<String, dynamic>?)?['display_name'] as String? ?? '',
      talker: (json['active_target'] as Map<String, dynamic>?)?['talker'] as String? ?? '',
      isGroup: (json['active_target'] as Map<String, dynamic>?)?['is_group'] as bool? ?? false,
    ),
    mode: json['mode'] == 'rapid' ? DesktopMode.rapid : DesktopMode.normal,
    rulePattern: json['rule_pattern'] as String? ?? '',
  );
}
```

```dart
// controller additions
Future<void> startServices() async {
  isBusy = true;
  notifyListeners();
  try {
    await _service.startServices();
    await initialize();
  } finally {
    isBusy = false;
    notifyListeners();
  }
}
```

- [ ] **Step 4: Run tests and verify GREEN**

Run: `flutter test test/windows_service_launcher_test.dart test/desktop_console_live_service_test.dart`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/features/desktop_console/data/http_desktop_service.dart lib/features/desktop_console/data/windows_service_launcher.dart lib/features/desktop_console/controller/desktop_console_controller.dart lib/features/desktop_console/presentation/desktop_console_page.dart test/windows_service_launcher_test.dart test/desktop_console_live_service_test.dart
git commit -m "feat(glacier): wire desktop console to local service"
```

### Task 5: Record continuity, run verification, and prepare the next milestone

**Files:**
- Create: `android/app/src/main/kotlin/com/super_ivan_pro/glacier/discussion_progress/wechat_automation_windows_desktop_progress_2026-04-23.md`
- Modify: `README.md`

- [ ] **Step 1: Write the failing documentation checklist**

```markdown
- [ ] README contains a Windows desktop development section
- [ ] Progress note records which desktop features are real and which are still stubbed
- [ ] Commands for Flutter UI and Python desktop service verification are written exactly once
```

- [ ] **Step 2: Run the planned verification commands**

Run:

```bash
flutter analyze
flutter test
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -v
```

Expected:

1. `flutter analyze` reports no errors.
2. `flutter test` passes for the new desktop shell tests.
3. Python tests pass, including the new desktop service tests.

- [ ] **Step 3: Write the minimal continuity docs**

```markdown
# WeChat Automation Windows Desktop Progress

Saved at: 2026-04-23

## Phase 1 completed

1. Flutter Windows single-page console is in place.
2. Python desktop service skeleton is reachable through local JSON endpoints.
3. Flutter can launch and stop the local service from one place.

## Still stubbed

1. `wechat-decrypt` child-process management.
2. Real packaging into a bundled Windows installable app.
3. Full live event streaming in the desktop UI.
```

- [ ] **Step 4: Commit**

```bash
git add README.md android/app/src/main/kotlin/com/super_ivan_pro/glacier/discussion_progress/wechat_automation_windows_desktop_progress_2026-04-23.md
git commit -m "docs(glacier): record desktop phase1 progress"
```

## Self-Review Checklist

Spec coverage:

1. Desktop single-page console: Tasks 1, 2, and 4.
2. One local Python service boundary: Task 3.
3. Local `%LOCALAPPDATA%` persistence direction: Task 3.
4. Service start or stop from Flutter: Task 4.
5. Local continuity docs and exact verification commands: Task 5.

Placeholder scan:

1. No unfinished placeholder markers remain in the tasks.
2. Every task includes exact file paths, commands, and commit messages.

Type consistency:

1. `DesktopService`, `DesktopSnapshot`, `ActiveTarget`, and `DesktopMode` are the shared names across the Flutter tasks.
2. `DesktopStateStore` and `create_app(...)` are the shared names across the Python tasks.

Execution note:

1. Execute Task 1 through Task 4 first.
2. Do not touch `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/config/arm_state.local.json`.
3. Do not touch `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/config/rules.local.json`.
