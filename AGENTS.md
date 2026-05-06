# AGENTS.md

This repository is a Flutter app with a Windows desktop console for local WeChat automation. Work carefully: the app can control real local processes and, when armed, can send real WeChat messages.

## Scope

- Primary app code is under `lib/features/desktop_console`.
- Python automation code is under `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation`.
- Local progress notes are under `android/app/src/main/kotlin/com/super_ivan_pro/glacier/discussion_progress`.
- Do not edit `android/app/src/main/kotlin/com/super_ivan_pro/glacier/discussion_progress/wechat_automation_windows_desktop_design_2026-04-22.md` unless the user explicitly asks.

## Safety Rules

- Do not operate the WeChat window or trigger real sending without explicit user approval.
- Before runtime validation, check `GET http://127.0.0.1:18090/status` and confirm `armed=false`.
- Do not arm the bot as part of routine tests.
- Do not commit local runtime files such as `arm_state.local.json`, `rules.local.json`, or `runtime.local.json`.
- Treat unrelated dirty files as user-owned; do not revert them.

## Runtime Model

- Flutter can lazily start `desktop_service.py` when the local HTTP service is unavailable.
- Opening the app does not automatically start `run_bot.py`.
- `POST /services/start` starts the managed process chain.
- If `wechat_decrypt_root` is configured and the watcher URL is not healthy, `desktop_service.py` starts `wechat-decrypt` before `run_bot.py`.
- `run_bot.py` only dispatches replies when `ArmStateStore.read().enabled` is true.

## Preferred Workflow

- Read the progress note before changing this area.
- Check `git status --short` before edits.
- Keep changes scoped to the requested surface.
- Update the progress note when implementation state or blockers change.
- Prefer tests that exercise the local service contract instead of real WeChat actions.

## Verification

Use these commands for normal validation:

```powershell
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter analyze
flutter test
```

Use `flutter build windows` when the change affects packaging, bundled assets, or Windows launcher behavior.
