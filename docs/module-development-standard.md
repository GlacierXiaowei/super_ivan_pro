# Optional Module Development Standard

This project uses build-time optional modules. Modules are source-level feature
packages that can be included in an edition build or left out completely. They
are not hot-loaded runtime plugins.

## Goals

- Keep core automation behavior stable.
- Let feature modules be added, removed, or combined by edition builds.
- Ensure a core build can exclude optional module code, assets, scripts, and
  config files.

## Core Boundary

Core may define only shared module infrastructure:

- module host UI
- shared module interfaces
- shared navigation or entry metadata
- shared visual components needed by multiple modules

Core must not import concrete optional modules unless the current edition is
intended to include them. A hidden button or `enabled=false` flag is not enough
to prove a module is excluded from a build.

## Module Boundary

Each optional module owns its own code and support files. Keep these under a
module-specific folder where practical, for example:

```text
lib/features/remote_control/
android/app/src/main/kotlin/com/super_ivan_pro/glacier/modules/remote_control/
tools/modules/remote_control/
```

Module code should communicate with core through stable interfaces or existing
local service contracts. Avoid direct writes to core state files unless the
module explicitly owns that state through a documented interface.

## Configuration

Modules must keep private configuration in their own files and include a schema
version. For example:

```json
{
  "schema_version": 1,
  "enabled": false
}
```

Do not add module-specific fields to core runtime JSON files such as:

- `runtime.local.json`
- `rules.local.json`
- `arm_state.local.json`

If a module needs to control existing automation behavior, call the local HTTP
service contract instead of editing those files directly.

## Safety Requirements

Any module that can affect networking, local processes, windows, clipboard,
input focus, or message sending must document:

- its default enabled state
- exposed ports or listeners
- authentication or token behavior
- whether it can arm real sending
- how it avoids accidental sends

Modules with real-send impact must default to a non-sending or disabled state
unless the user explicitly approves otherwise.

## Tests

Module tests should prove both normal behavior and isolation:

- module logic works when included
- core behavior works without the module
- module-specific JSON does not break existing core parsers
- edition packaging includes only the intended module assets
