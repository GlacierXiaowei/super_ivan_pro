# Core Module Host Design

This document defines the core-side module host for build-time optional
modules. It is the next layer below the optional module standards and does not
define any concrete remote-control feature.

## Purpose

The core app needs a small, stable place where edition builds can register
optional features. The goal is to let the project ship:

- a core build with no optional module code or assets
- a remote-enabled build that includes a remote-control module
- future editions that combine several independent modules

The module host is not a hot-loading plugin runtime. Module inclusion is decided
by source composition and packaging on an edition branch.

## Main Branch Boundary

`main` should contain only:

- the shared module interface
- an empty or core-only module registry
- generic module host UI, if the app needs a visible entry point
- tests that prove the core app works with no optional modules

`main` must not import concrete optional modules such as a future
remote-control implementation. If a file in `main` imports
`lib/features/remote_control/` or a module-specific Python package, the boundary
has already been broken.

## Core API Shape

The core module interface should stay narrow and UI-oriented at first. A module
can describe how it appears in the app and can provide an entry widget or action
through a shared contract. The first version should avoid exposing automation
internals directly.

Recommended Dart-side concepts:

- `AppModule`: immutable module descriptor
- `ModuleEntry`: label, icon, route or builder, and optional status metadata
- `ModuleRegistry`: edition-owned list of included modules
- `ModuleHostPage`: generic screen that renders registered entries

The core registry in `main` should return an empty list until a concrete edition
chooses to include modules.

## Edition Registry

Each edition owns its registry composition. A core edition should compile
without optional module imports. A module-enabled edition may replace or extend
the registry with imports for selected modules.

Preferred shape:

```text
lib/core/modules/
  app_module.dart
  module_registry.dart
  module_host_page.dart

lib/editions/
  core/module_registry.dart
  remote/module_registry.dart
```

The exact paths can change during implementation if the existing Flutter
structure suggests a better fit. The important rule is that core imports only
the shared interface and the selected edition registry.

## Packaging Boundary

Registering a module in Flutter is not enough. Edition packaging must also
include or exclude the matching support files:

- Flutter assets in `pubspec.yaml`
- Python scripts and packages
- config templates
- Windows helper scripts
- user-facing docs for that edition

For a core build, remote-control files should not appear in the source tree used
for packaging, the Flutter asset list, or the final distribution.

## Configuration Boundary

Core runtime files must stay module-neutral. Optional modules should use
module-owned config files with `schema_version`, for example:

```text
remote_control.local.json
```

Module-specific settings must not be added to:

- `runtime.local.json`
- `rules.local.json`
- `arm_state.local.json`

If a module needs to affect automation behavior, it should call the documented
local HTTP service contract rather than editing core JSON directly.

## Remote-Control Module Implications

The future Tailscale remote-control module should be a consumer of this module
host, not a reason to widen core.

Expected placement:

```text
lib/features/remote_control/
android/app/src/main/kotlin/com/super_ivan_pro/glacier/modules/remote_control/
tools/modules/remote_control/
```

Expected behavior:

- Tailscale provides private network reachability only.
- The app or local Python side still owns a narrow remote gateway.
- The existing local service on `127.0.0.1:18090` should not be exposed
  directly.
- Safe remote actions should start with status, start, stop, restart, and
  disarm.
- Remote arming should be disabled by default or require a separate explicit
  approval flow.

## Error Handling

The module host should treat modules as optional entries:

- if no modules are registered, the host shows an empty state or hides the
  module entry entirely
- if a module entry fails to open, the error is contained to that module surface
- core automation controls continue to work even when no module registry entries
  exist

The core app should not read module config files during startup unless that
module is included by the edition.

## Tests And Checks

The first implementation should include focused checks for the boundary:

- the core registry has no optional modules by default
- the app can render or start with an empty module registry
- core JSON parsers do not require module-specific fields
- no core file imports a concrete optional module

Edition builds should add their own checks:

- included modules are registered
- excluded modules are absent from registry and package inputs
- packaging still verifies `armed=false` before real-device validation

## Initial Implementation Plan

The minimal first implementation on `main` should be:

1. Add the shared Dart module interface.
2. Add a core registry that returns no optional modules.
3. Add a small module host entry only if it can be added without changing the
   desktop console behavior.
4. Add tests or static checks for empty-registry behavior and import isolation.

The remote-control module should be developed later on a module or edition
branch after this core boundary is stable.
