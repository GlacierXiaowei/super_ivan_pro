# Edition Build Standard

Edition branches define product variants. They combine core code with selected
optional modules and are the source for release builds.

## Branch Roles

- `main` or a core branch: core system, module host, shared interfaces.
- `module/<name>`: focused development for one optional module.
- `edition/<name>`: selected modules combined for packaging and release.

Module branches are for development. Edition branches are for composition and
packaging.

## Recommended Editions

Common edition examples:

```text
main
  Core build only.

edition/remote
  Core plus remote-control module.

edition/full
  Core plus all selected optional modules.
```

Use release tags to record shipped outputs, for example `v1.1.0-core`,
`v1.1.0-remote`, or `v1.1.0-full`.

## Build Manifest

Each edition should have a short manifest or documentation section that states:

- edition name
- included modules
- excluded modules if exclusion matters
- module registry file or generation source
- asset sources included in the package
- verification commands

If the project later adds generation scripts, the manifest should generate the
edition registry and asset list rather than requiring every module branch to
edit the same files.

## Inclusion and Exclusion Checks

Every edition build must verify the intended module boundary:

- Core builds do not contain optional module code, scripts, config templates, or
  assets.
- Module-enabled builds contain only the modules listed by that edition.
- Remote or process-control modules are disabled by default unless the edition
  explicitly documents another behavior.

For this WeChat automation app, runtime validation must still check
`GET http://127.0.0.1:18090/status` and confirm `armed=false` before any
real-device validation.

## Packaging Risk Areas

Pay special attention to files that are commonly shared across modules:

- `pubspec.yaml`
- module registry files
- Windows packaging scripts
- helper script directories
- runtime config seed files

Edition branches should own these composition changes so module branches remain
focused and easier to merge.
