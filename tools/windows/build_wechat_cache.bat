@echo off
setlocal

set "PYTHON_EXE=python"
if not "%SUPER_IVAN_DESKTOP_PYTHON%"=="" set "PYTHON_EXE=%SUPER_IVAN_DESKTOP_PYTHON%"

echo Building WeChat decrypted history cache...

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$configPath=Join-Path $env:LOCALAPPDATA 'SuperIvanPro\wechat_automation\config\runtime.local.json';" ^
  "if (-not (Test-Path -LiteralPath $configPath)) { throw ('runtime.local.json not found: ' + $configPath) }" ^
  "$config=Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json;" ^
  "$root=[string]$config.wechat_decrypt_root;" ^
  "if (-not $root) { $root=$env:SUPER_IVAN_WECHAT_DECRYPT_ROOT }" ^
  "if (-not $root) { throw 'wechat_decrypt_root is not configured in runtime.local.json.' }" ^
  "$main=Join-Path $root 'main.py';" ^
  "if (-not (Test-Path -LiteralPath $main)) { throw ('main.py not found under wechat_decrypt_root: ' + $root) }" ^
  "Write-Host ('wechat_decrypt_root=' + $root);" ^
  "Push-Location -LiteralPath $root;" ^
  "try { & $env:PYTHON_EXE 'main.py' 'decrypt'; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } } finally { Pop-Location }"

if errorlevel 1 (
  echo Failed to build WeChat cache.
  exit /b 1
)

echo WeChat cache build finished.
exit /b 0
