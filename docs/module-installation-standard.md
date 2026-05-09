# Optional Module Installation Standard

In this repository, "installing" a module means adding it to an edition branch
for a build. It does not mean runtime hot loading.

## Installation Flow

1. Start from the intended edition branch, not from an unrelated module branch.
2. Merge or cherry-pick the module implementation.
3. Register the module in that edition's module registry.
4. Add only the module's required assets, scripts, and config templates.
5. Update edition documentation to list the included module.
6. Run validation for both the module and the unchanged core behavior.

## Registry Rules

The module registry is edition-owned. A core-only edition should not import
optional module implementations. A module-enabled edition may register concrete
module classes.

Prefer separate registry files or generated registry output per edition instead
of one global registry that imports every module.

## Asset Rules

Adding a module to UI is not enough. The edition must also explicitly include
or exclude related assets:

- Flutter asset entries
- Python scripts
- config examples
- Windows helper scripts
- packaging script inputs

Core editions must not ship optional module assets.

## Configuration Rules

Module installation may create or seed module-owned config files. It must not
migrate module settings into core automation config files.

If a module depends on a core service setting, store only the module side of the
configuration in the module config and call the existing service API at runtime.

## Removal Flow

To remove a module from an edition:

1. Remove it from the edition registry.
2. Remove its assets and helper scripts from packaging inputs.
3. Remove edition docs that claim the feature is available.
4. Verify the package no longer contains the module code or assets.
5. Verify core automation still starts, reports status, and remains disarmed.

Do not delete shared core interfaces simply because one module is removed.
