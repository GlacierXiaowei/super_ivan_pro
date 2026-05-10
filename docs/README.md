# Documentation Index

All non-README project documents live under `docs/`. Folder-level `README.md`
files stay next to the code they explain. `AGENTS.md` stays at the repository
root because the tooling reads it from there.

## Read Order

1. `../AGENTS.md`
2. `../README.md`
3. `progress/wechat_automation_windows_desktop_progress_2026-04-23.md`
4. For optional module work, read the three module and edition standards below
5. The most relevant file under `plans/` or `progress/` for the task at hand

## Layout

- `progress/`: continuity notes, status snapshots, and design docs
- `plans/`: implementation plans and staged execution notes
- `module-development-standard.md`: optional module development boundaries
- `module-installation-standard.md`: edition-level module installation/removal
- `edition-build-standard.md`: multi-edition branch, build, and verification rules
- `core-module-host-design.md`: core-side module host design for edition modules
- `windows-portable-distribution.md`: Windows portable packaging notes
- `windows-portable-user-guide.zh-CN.md`: tester-facing Windows usage guide

## Editing Rules

- New non-README project docs should be added under `docs/`.
- Keep code-local `README.md` files in their existing folders.
- Treat `progress/wechat_automation_windows_desktop_design_2026-04-22.md` as
  protected unless the user explicitly asks to edit it.
