# Windows Portable Distribution

This project currently targets Windows desktop distribution only.

## Expected package layout

The portable package should contain at least:

```text
SuperIvanPro-Windows-Portable/
  super_ivan_pro.exe
  flutter_windows.dll
  data/
  tools/windows/
  restart_python_service.bat
  build_wechat_cache.bat
  init_first_run.bat
```

The package no longer bundles Python. Test machines must install Python 3 and
make either `python` or `py` available from the command line.

To avoid manual `wechat-decrypt` setup, include:

```text
runtime/
  wechat-decrypt/
    main.py
```

## What the current app can auto-detect

The current code now auto-detects this packaged location when present:

- `runtime/wechat-decrypt/main.py`

The Windows helper scripts also understand both:

- Release root execution, such as `Release\restart_python_service.bat`
- Nested tool execution, such as `Release\tools\windows\restart_python_service.bat`

## Recommended user flow

1. Extract the ZIP to a normal writable folder.
2. Log in to Windows WeChat first.
3. Run `init_first_run.bat` once.
4. Start `super_ivan_pro.exe`.
5. Keep `armed=false` during basic environment checks.
6. If the local Python wrapper gets stuck, run `restart_python_service.bat`.
7. If history search is stale, run `build_wechat_cache.bat`.

## Developer packaging command

Build the Windows app first:

```powershell
flutter build windows
```

Then assemble a portable directory:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\package_portable_release.ps1 `
  -WechatDecryptRoot "C:\path\to\wechat-decrypt" `
  -CreateZip
```

## Responsibility split

What Codex can do in-repo:

- keep the Windows build output deterministic
- keep helper scripts working from packaged paths
- add packaging scripts and docs
- make the app prefer bundled `wechat-decrypt` locations

What still needs a human decision or input:

- which exact `wechat-decrypt` directory should be bundled
- whether target testers have Python 3 installed
- final tester-facing wording and delivery channel
