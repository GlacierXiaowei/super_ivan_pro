# Core Module Host Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the minimal core-side module host so `main` can compile with zero optional modules while edition branches can register build-time modules later.

**Architecture:** Core defines only shared Dart module interfaces and a generic host page. The active edition registry is a narrow composition file that is empty on `main`; future edition branches may edit that file to import concrete modules. The existing desktop console remains the default home when no modules are registered.

**Tech Stack:** Flutter, Dart, Material widgets, `flutter_test`.

---

## Files

- Create: `lib/core/modules/app_module.dart`
  - Owns the shared module descriptor used by all edition modules.
- Create: `lib/core/modules/module_host_page.dart`
  - Owns the optional module navigation shell used only when modules are present.
- Create: `lib/edition/module_registry.dart`
  - Owns the active edition's module list. On `main`, it returns no modules and imports no optional feature code.
- Modify: `lib/app/app.dart`
  - Reads the active edition registry and switches between the current desktop console and the module host.
- Create: `test/module_registry_test.dart`
  - Proves `main` has an empty module registry.
- Create: `test/module_host_page_test.dart`
  - Proves the app still renders the desktop console with no modules and can render a synthetic module when injected.
- Create: `test/module_import_isolation_test.dart`
  - Proves core and edition registry files do not import the future remote-control module.

Do not modify Python service files, `pubspec.yaml`, runtime JSON files, or Windows packaging files in this first pass.

---

### Task 1: Add Shared Module Descriptor

**Files:**
- Create: `lib/core/modules/app_module.dart`
- Test: `test/module_registry_test.dart`

- [ ] **Step 1: Write the failing empty-registry test**

Create `test/module_registry_test.dart`:

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/edition/module_registry.dart';

void main() {
  test('main edition registers no optional modules', () {
    expect(buildEditionModules(), isEmpty);
  });
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
flutter test test/module_registry_test.dart
```

Expected: FAIL because `package:super_ivan_pro/edition/module_registry.dart` does not exist.

- [ ] **Step 3: Add the module descriptor**

Create `lib/core/modules/app_module.dart`:

```dart
import 'package:flutter/material.dart';

class AppModule {
  const AppModule({
    required this.id,
    required this.title,
    required this.icon,
    required this.builder,
    this.description,
  });

  final String id;
  final String title;
  final String? description;
  final IconData icon;
  final WidgetBuilder builder;

  Widget build(BuildContext context) => builder(context);
}
```

- [ ] **Step 4: Add the empty main registry**

Create `lib/edition/module_registry.dart`:

```dart
import 'package:super_ivan_pro/core/modules/app_module.dart';

const List<AppModule> _mainEditionModules = <AppModule>[];

List<AppModule> buildEditionModules() {
  return _mainEditionModules;
}
```

- [ ] **Step 5: Run the focused registry test**

Run:

```powershell
flutter test test/module_registry_test.dart
```

Expected: PASS with one passing test.

- [ ] **Step 6: Commit this task**

```powershell
git add lib/core/modules/app_module.dart lib/edition/module_registry.dart test/module_registry_test.dart
git commit -m "feat: add empty edition module registry"
```

---

### Task 2: Add Generic Module Host Page

**Files:**
- Create: `lib/core/modules/module_host_page.dart`
- Test: `test/module_host_page_test.dart`

- [ ] **Step 1: Write the failing synthetic-module host test**

Create `test/module_host_page_test.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/app/app.dart';
import 'package:super_ivan_pro/core/modules/app_module.dart';
import 'package:super_ivan_pro/features/desktop_console/data/fake_desktop_service.dart';

void main() {
  testWidgets('renders the existing desktop console when no modules exist', (
    tester,
  ) async {
    await tester.pumpWidget(
      SuperIvanDesktopApp(
        service: FakeDesktopService.seed(),
        modules: const <AppModule>[],
      ),
    );

    expect(find.text('微信自动化桌面端'), findsOneWidget);
    expect(find.text('服务状态'), findsOneWidget);
    expect(find.byType(NavigationRail), findsNothing);
  });

  testWidgets('renders an injected module through the module host', (
    tester,
  ) async {
    final modules = <AppModule>[
      AppModule(
        id: 'synthetic',
        title: '测试模块',
        description: 'Only used by widget tests.',
        icon: Icons.extension,
        builder: (_) => const Center(child: Text('测试模块内容')),
      ),
    ];

    await tester.pumpWidget(
      SuperIvanDesktopApp(
        service: FakeDesktopService.seed(),
        modules: modules,
      ),
    );

    expect(find.byType(NavigationRail), findsOneWidget);
    expect(find.text('控制台'), findsOneWidget);
    expect(find.text('测试模块'), findsOneWidget);

    await tester.tap(find.text('测试模块'));
    await tester.pumpAndSettle();

    expect(find.text('测试模块内容'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
flutter test test/module_host_page_test.dart
```

Expected: FAIL because `SuperIvanDesktopApp` does not accept `modules` and `ModuleHostPage` does not exist.

- [ ] **Step 3: Add the module host page**

Create `lib/core/modules/module_host_page.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:super_ivan_pro/core/modules/app_module.dart';

class ModuleHostPage extends StatefulWidget {
  const ModuleHostPage({
    super.key,
    required this.desktopConsole,
    required this.modules,
  });

  final Widget desktopConsole;
  final List<AppModule> modules;

  @override
  State<ModuleHostPage> createState() => _ModuleHostPageState();
}

class _ModuleHostPageState extends State<ModuleHostPage> {
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    final destinations = <NavigationRailDestination>[
      const NavigationRailDestination(
        icon: Icon(Icons.desktop_windows_outlined),
        selectedIcon: Icon(Icons.desktop_windows),
        label: Text('控制台'),
      ),
      for (final module in widget.modules)
        NavigationRailDestination(
          icon: Icon(module.icon),
          label: Text(module.title),
        ),
    ];
    final pages = <Widget>[
      widget.desktopConsole,
      for (final module in widget.modules) module.build(context),
    ];

    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: _selectedIndex,
            labelType: NavigationRailLabelType.all,
            destinations: destinations,
            onDestinationSelected: (index) {
              setState(() {
                _selectedIndex = index;
              });
            },
          ),
          const VerticalDivider(width: 1),
          Expanded(
            child: IndexedStack(
              index: _selectedIndex,
              children: pages,
            ),
          ),
        ],
      ),
    );
  }
}
```

- [ ] **Step 4: Run the host test to verify it still fails at app wiring**

Run:

```powershell
flutter test test/module_host_page_test.dart
```

Expected: FAIL because `SuperIvanDesktopApp` still does not accept `modules`.

- [ ] **Step 5: Commit this task**

```powershell
git add lib/core/modules/module_host_page.dart test/module_host_page_test.dart
git commit -m "feat: add generic module host page"
```

---

### Task 3: Wire The Host Into The App Shell

**Files:**
- Modify: `lib/app/app.dart`
- Test: `test/module_host_page_test.dart`
- Test: `test/app_bootstrap_test.dart`
- Test: `test/widget_test.dart`

- [ ] **Step 1: Update `SuperIvanDesktopApp` to accept injected modules**

Modify `lib/app/app.dart` to:

```dart
import 'package:flutter/material.dart';
import 'package:super_ivan_pro/app/theme.dart';
import 'package:super_ivan_pro/core/modules/app_module.dart';
import 'package:super_ivan_pro/core/modules/module_host_page.dart';
import 'package:super_ivan_pro/edition/module_registry.dart';
import 'package:super_ivan_pro/features/desktop_console/data/desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/data/http_desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/desktop_console_page.dart';

class SuperIvanDesktopApp extends StatelessWidget {
  const SuperIvanDesktopApp({
    super.key,
    DesktopService? service,
    List<AppModule>? modules,
  }) : _service = service,
       _modules = modules;

  final DesktopService? _service;
  final List<AppModule>? _modules;

  @override
  Widget build(BuildContext context) {
    final service = _service ?? HttpDesktopService.development();
    final modules = _modules ?? buildEditionModules();
    final desktopConsole = DesktopConsolePage(service: service);

    return MaterialApp(
      title: '微信自动化桌面端',
      debugShowCheckedModeBanner: false,
      theme: buildDesktopTheme(),
      home: modules.isEmpty
          ? desktopConsole
          : ModuleHostPage(
              desktopConsole: desktopConsole,
              modules: modules,
            ),
    );
  }
}
```

- [ ] **Step 2: Run the new host tests**

Run:

```powershell
flutter test test/module_host_page_test.dart
```

Expected: PASS.

- [ ] **Step 3: Run the existing app bootstrap tests**

Run:

```powershell
flutter test test/app_bootstrap_test.dart test/widget_test.dart
```

Expected: PASS. These tests prove the empty-registry main build still opens the desktop console directly.

- [ ] **Step 4: Commit this task**

```powershell
git add lib/app/app.dart test/module_host_page_test.dart
git commit -m "feat: wire edition modules into desktop app"
```

---

### Task 4: Add Import-Isolation Guard

**Files:**
- Create: `test/module_import_isolation_test.dart`
- Test: `test/module_import_isolation_test.dart`

- [ ] **Step 1: Write the import-isolation test**

Create `test/module_import_isolation_test.dart`:

```dart
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('main module host files do not import remote-control code', () {
    final guardedFiles = <String>[
      'lib/app/app.dart',
      'lib/core/modules/app_module.dart',
      'lib/core/modules/module_host_page.dart',
      'lib/edition/module_registry.dart',
    ];

    for (final path in guardedFiles) {
      final contents = File(path).readAsStringSync();

      expect(
        contents,
        isNot(contains('features/remote_control')),
        reason: '$path must not import a concrete remote-control module.',
      );
      expect(
        contents,
        isNot(contains('modules/remote_control')),
        reason: '$path must not import remote-control Python/module paths.',
      );
    }
  });
}
```

- [ ] **Step 2: Run the isolation test**

Run:

```powershell
flutter test test/module_import_isolation_test.dart
```

Expected: PASS.

- [ ] **Step 3: Commit this task**

```powershell
git add test/module_import_isolation_test.dart
git commit -m "test: guard core module import isolation"
```

---

### Task 5: Run Full Validation

**Files:**
- No source files should be created in this task.

- [ ] **Step 1: Run Flutter analysis**

Run:

```powershell
flutter analyze
```

Expected: PASS with no issues.

- [ ] **Step 2: Run Flutter tests**

Run:

```powershell
flutter test
```

Expected: PASS for the full Flutter test suite.

- [ ] **Step 3: Run Python service tests**

Run:

```powershell
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
```

Expected: PASS. This change should not touch Python behavior, but the check proves the core automation contract still holds.

- [ ] **Step 4: Review the final diff**

Run:

```powershell
git diff --stat
git diff -- lib/app/app.dart lib/core/modules lib/edition test
```

Expected: only the module host files, app shell wiring, and tests are changed. No Python service files, runtime JSON files, packaging scripts, or remote-control files should appear.

- [ ] **Step 5: Commit final fixes if validation required small adjustments**

If validation required a correction, commit only those correction files:

```powershell
git add lib/app/app.dart lib/core/modules lib/edition test
git commit -m "fix: stabilize core module host"
```

If no correction was needed after Task 4, skip this commit.

---

## Self-Review

- Spec coverage: this plan implements the shared module interface, empty main registry, generic host behavior, import isolation, and no-module default behavior from `docs/core-module-host-design.md`.
- Scope boundary: this plan does not implement Tailscale, remote listeners, remote-control config, Python gateways, or edition packaging.
- Type consistency: `AppModule`, `buildEditionModules`, `ModuleHostPage`, and `SuperIvanDesktopApp.modules` use the same names across all tasks.
- Safety boundary: this plan does not arm the bot, call live WeChat, expose `127.0.0.1:18090`, or edit runtime JSON files.
